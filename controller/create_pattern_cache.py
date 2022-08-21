import argparse
import json
import asyncio

from core.pattern_cache import PatternCache
from patterns import pattern_config


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--led_config", type=argparse.FileType('r'),
                        default="../config/led_config.json", help="LED config file")
    parser.add_argument("-a", "--animation_rate", type=int, default=20, help="The target animation rate in Hz")
    parser.add_argument("-f", "--force_update", action='store_true', 
                        help="Forces update of all cached patterns. Otherwise will only update missing or incomplete patterns.")
    parser.add_argument("-m", "--max_cached_pattern_duration", type=int, default=600, 
                        help="The maximum duration a pattern is cached for")
    args = parser.parse_args()
    led_config = json.load(args.led_config)

    cache = PatternCache(pattern_config.DEFAULT_CONFIG, led_config, args.animation_rate)

    patterns = []
    for _, cls, params in cache.pattern_config:
        pattern = cls()
        for key in params:
            setattr(pattern.params, key, params[key])
        pattern.prepareSegments(led_config)
        pattern.initialize()
        patterns.append(pattern)
        
    await cache.build_cache(patterns, args.max_cached_pattern_duration, args.force_update)

asyncio.run(main())
