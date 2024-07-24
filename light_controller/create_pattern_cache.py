import argparse
import json
import asyncio

from core.pattern_cache import PatternCache
from patterns import pattern_config
from impossible_dialogue.config import HeadConfigs


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--config", type=argparse.FileType('r'), default="../config/head_config.json", 
                        help="LED config file")
    parser.add_argument("-a", "--animation_rate", type=int,
                        default=20, help="The target animation rate in Hz")
    parser.add_argument("-f", "--force_update", action='store_true',
                        help="Forces update of all cached patterns. Otherwise will only update missing or incomplete patterns.")
    parser.add_argument("-m", "--max_cached_pattern_duration", type=int, default=60,
                        help="The maximum duration a pattern is cached for")
    args = parser.parse_args()
    config = json.load(args.config)
    head_configs = HeadConfigs(config["heads"])

    for head_id, head_config in head_configs.heads.items():
        if not head_config.led_config:
            continue
        led_config_file = open(head_config.led_config)
        led_config = json.load(led_config_file)
        cache = PatternCache(led_config, args.animation_rate)

        # Initialize all patterns
        patterns = {}
        for pattern_id in pattern_config.PATTERNS.keys():
            pattern = pattern_config.pattern_factory(pattern_id)
            pattern.prepareSegments(led_config)
            pattern.initialize()
            patterns[pattern_id] = pattern
        print(head_id)
        await cache.build_cache(patterns, args.max_cached_pattern_duration, args.force_update)

asyncio.run(main())
