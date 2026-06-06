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
                           out_dir=args.out, enhance=args.enhance)
    for p in paths:
        print(p)
    return 0


def _cmd_ppt(args: argparse.Namespace) -> int:
    from cgimg.ppt.builder import build_pptx
    print(build_pptx(args.images, args.out, aspect=args.aspect))
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
    g.set_defaults(func=_cmd_gen, enhance=True)

    pp = sub.add_parser("ppt")
    pp.add_argument("images", nargs="+")
    pp.add_argument("--out", default="deck.pptx")
    pp.add_argument("--aspect", default="16:9")
    pp.set_defaults(func=_cmd_ppt)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
