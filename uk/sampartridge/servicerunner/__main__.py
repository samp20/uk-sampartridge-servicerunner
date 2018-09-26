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
    config.read_file(open(args.config))
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

if __name__ == '__main__':
    main()