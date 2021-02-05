import argparse
import logging
import os
import sys
import time

import pyautogui
import yaml

parser = argparse.ArgumentParser(description='Get the active window title and write it to disk')
parser.add_argument('--sleep', help='Number for seconds to sleep before getting active window title', type=int,
                    default=5)
args = parser.parse_args()

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(message)s')

pyautogui.FAILSAFE = False

logging.info(f'You have {args.sleep} seconds to open the game, starting now')
time.sleep(args.sleep)

title = str(pyautogui.getActiveWindowTitle()).strip().replace('\u200b', '')
logging.info(f'Adding window title: "{title}"')

yamlFilePath = os.path.join(os.getcwd(), '0xQWERTY-active-window-titles.yaml')
# Read existing file if there is one
titles = []
if os.path.isfile(yamlFilePath):
    with open(yamlFilePath, 'r') as yamlFile:
        titles = yaml.safe_load(yamlFile)

# Add current title
titles.append(title)

# Write results to disk
with open(yamlFilePath, 'w') as yamlFile:
    yaml.dump(titles, yamlFile)

logging.info('You can now close this window')
time.sleep(30)
