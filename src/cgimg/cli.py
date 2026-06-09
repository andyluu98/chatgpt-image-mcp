"""cgimg CLI: login / gen / ppt."""
from __future__ import annotations
import argparse
import sys


def _cmd_login(args: argparse.Namespace) -> int:
    from cgimg.auth import oauth_login, tokens
    if args.callback:
        oauth_login.complete(args.callback)
        print(f"[OK] Logged in. Saved to {tokens._auth_path()}")
        return 0
    url = oauth_login.build_and_stash(args.email or "")
    print("\n1. A browser should have opened. If not, open this URL:\n")
    print("   " + url + "\n")
    print("2. Log into ChatGPT. You'll land on a platform.openai.com page (may say 'Oops').")
    print("3. Copy the FULL URL from the address bar, then run:\n")
    print('   cgimg login --callback "<paste the URL here>"\n')
    return 0


def _cmd_gen(args: argparse.Namespace) -> int:
    from cgimg.engine.generate import generate_image
    paths = generate_image(args.prompt, aspect=args.aspect, n=args.n,
                           out_dir=args.out, enhance=args.enhance, style=args.style)
    for p in paths:
        print(p)
    return 0


def _cmd_ppt(args: argparse.Namespace) -> int:
    from cgimg.ppt.builder import build_pptx
    print(build_pptx(args.images, args.out, aspect=args.aspect))
    return 0


def _cmd_branded(args: argparse.Namespace) -> int:
    from cgimg.branding.deck import branded_deck
    result = branded_deck(args.logo_path, args.prompts, aspect=args.aspect,
                          out_pptx=args.out, out_dir=args.out_dir,
                          logo_position=args.position, logo_scale=args.scale)
    print(f"deck: {result['path']}")
    print(f"brand_colors: {', '.join(result['brand_colors'])}")
    for p in result["image_paths"]:
        print(p)
    return 0


def _cmd_styled(args: argparse.Namespace) -> int:
    from cgimg.branding.deck import styled_deck
    result = styled_deck(args.ref_image, args.prompts, aspect=args.aspect,
                         out_pptx=args.out, out_dir=args.out_dir)
    print(f"deck: {result['path']}")
    print(f"brand_colors: {', '.join(result['brand_colors'])}")
    for p in result["image_paths"]:
        print(p)
    return 0


def _cmd_research(args: argparse.Namespace) -> int:
    from cgimg.research.channels import research_topic
    plats = args.platforms.split(",") if args.platforms else None
    res = research_topic(args.topic, platforms=plats, out_path=args.out)
    print(res["brief_path"])
    for ins in res["insights"]:
        print(f"- [{ins['platform']}] {ins['title']}")
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    from cgimg.research.doctor import check_channels
    for k, v in check_channels().items():
        print(f"{k}: {v}")
    return 0


def _cmd_read(args: argparse.Namespace) -> int:
    from cgimg.research.channels import read_url
    r = read_url(args.url)
    print(r.get("title", ""))
    print(r.get("text", "")[:2000])
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cgimg")
    sub = p.add_subparsers(dest="cmd", required=True)

    lg = sub.add_parser("login")
    lg.add_argument("--callback", default=None, help="callback URL or code (step 2)")
    lg.add_argument("--email", default=None, help="optional email hint")
    lg.set_defaults(func=_cmd_login)

    g = sub.add_parser("gen")
    g.add_argument("prompt")
    g.add_argument("--aspect", default="16:9")
    g.add_argument("--n", type=int, default=1)
    g.add_argument("--out", default="out")
    g.add_argument("--no-enhance", dest="enhance", action="store_false",
                   help="skip auto-expanding the prompt via the ChatGPT text path")
    g.add_argument("--style", default="auto", choices=["auto", "slide", "fintech"],
                   help="'slide' = clean editorial; 'fintech' = light-blue dashboard")
    g.set_defaults(func=_cmd_gen, enhance=True)

    pp = sub.add_parser("ppt")
    pp.add_argument("images", nargs="+")
    pp.add_argument("--out", default="deck.pptx")
    pp.add_argument("--aspect", default="16:9")
    pp.set_defaults(func=_cmd_ppt)

    br = sub.add_parser("branded")
    br.add_argument("logo_path")
    br.add_argument("--prompts", nargs="+", required=True)
    br.add_argument("--out", default="deck.pptx")
    br.add_argument("--out-dir", dest="out_dir", default="out")
    br.add_argument("--aspect", default="16:9")
    br.add_argument("--position", default="top-left")
    br.add_argument("--scale", type=float, default=0.15)
    br.set_defaults(func=_cmd_branded)

    st = sub.add_parser("styled")
    st.add_argument("ref_image")
    st.add_argument("--prompts", nargs="+", required=True)
    st.add_argument("--out", default="deck.pptx")
    st.add_argument("--out-dir", dest="out_dir", default="out")
    st.add_argument("--aspect", default="16:9")
    st.set_defaults(func=_cmd_styled)

    rs = sub.add_parser("research")
    rs.add_argument("topic")
    rs.add_argument("--platforms", default=None, help="comma-separated, e.g. youtube,x")
    rs.add_argument("--out", default="out/brief.md")
    rs.set_defaults(func=_cmd_research)

    dr = sub.add_parser("doctor")
    dr.set_defaults(func=_cmd_doctor)

    rd = sub.add_parser("read")
    rd.add_argument("url")
    rd.set_defaults(func=_cmd_read)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
