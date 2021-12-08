import argparse
from scrape import ScraperJob
import json


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # Add an argument
    parser.add_argument('--url', '-u', type=str, default="https://nearme.vip/restaurant/us/pizza-restaurant/square-pie-guys-of-san-francisco/")
    args = parser.parse_args()

    job = ScraperJob(max_pages=20)
    job.scrape(args.url)
    print(json.dumps(job.results, indent=3))
    print("Results: {}".format(len(job.results)))
    print("Links Available: {}".format(len(job.queue)))