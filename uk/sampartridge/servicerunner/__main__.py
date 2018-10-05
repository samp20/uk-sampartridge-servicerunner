import argparse
import configparser
import os.path
import asyncio
from .runner import Runner
import logging

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="Configuration file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    config = configparser.ConfigParser()
    load_config(config, args.config)

    runner = Runner(config)
    runner.load_services()

    loop = asyncio.get_event_loop()
    try:
        loop.create_task(runner.start(loop))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(runner.stop())
        if hasattr(loop, 'shutdown_asyncgens'):
            loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

def load_config(parser, path):
    with open(path, 'rb') as f:
        parser.read_file(f)
        incs = parser.get('General', 'includes', fallback=None)
        if incs is not None:
            del parser['General']['includes']
            dirname = os.path.dirname(path)
            for pth in incs.split('\n'):
                pth = os.path.join(dirname, pth.strip())
                load_config(parser, pth)

if __name__ == '__main__':
    main()