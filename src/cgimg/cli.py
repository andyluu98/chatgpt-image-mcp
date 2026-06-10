"""cgimg CLI: login / gen / ppt / branded / styled."""
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
                           out_dir=args.out, enhance=args.enhance, style=args.style,
                           ref_image=args.ref_image, ref_mode=args.ref_mode)
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
    g.add_argument("--ref-image", dest="ref_image", default=None,
                   help="path to a reference image the model SEES while drawing")
    g.add_argument("--ref-mode", dest="ref_mode", default="style",
                   choices=["style", "logo", "asset"],
                   help="'logo'/'asset' = place that real logo into the image; "
                        "'style' = borrow only its look (default)")
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

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
