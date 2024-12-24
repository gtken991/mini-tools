"""
Bilibili Subtitle Downloader

This module provides functionality to download and convert subtitles from Bilibili videos.
It supports both short and long URLs, handles multiple parts (P), and converts JSON subtitles to SRT format.

Features:
- Async download support
- Automatic retry mechanism
- Short URL resolution
- Multi-part video support
- JSON to SRT conversion
"""

import os
import time
import math
import requests
import json
import re
import hashlib
from urllib.parse import urlencode
from tenacity import retry, stop_after_attempt, wait_fixed
import logging
import aiohttp
import asyncio
from dataclasses import dataclass
from aiohttp import ClientTimeout
from aiohttp_retry import RetryClient, ExponentialRetry

logger = logging.getLogger(__name__)

@dataclass
class SubtitleInfo:
    """
    Data class for storing subtitle information
    
    Attributes:
        url (str): The URL of the subtitle file
        lang (str): Language code of the subtitle
        title (str): Title of the video part
    """
    url: str
    lang: str
    title: str

class BilibiliSubtitle:
    """
    Main class for handling Bilibili subtitle downloads
    
    This class manages authentication, API requests, and subtitle downloads
    using asynchronous operations and retry mechanisms.
    """
    
    def __init__(self):
        """
        Initialize the subtitle downloader with default configurations
        Sets up timeout, retry options, session headers, and loads cookies
        """
        self.timeout = ClientTimeout(total=30)
        self.retry_options = ExponentialRetry(
            attempts=3,
            start_timeout=1,
            max_timeout=10,
            factor=2.0
        )
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://www.bilibili.com',
            'Connection': 'keep-alive'
        }
        # Mixin key table for WBI signature (subject to change)
        self.MIXIN_KEY_TABLE = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
            33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
            61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
            36, 20, 34, 44, 52
        ]
        # Load authentication cookies from config
        self.load_cookies()

    def load_cookies(self):
        """
        Load authentication cookies from config file
        
        Reads the cookie string from config.json, parses it into a dictionary,
        and updates the session cookies. Handles file existence and format validation.
        """
        try:
            # Check if config file exists
            if not os.path.exists('config.json'):
                logger.error("Config file config.json not found")
                return

            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Get and clean cookie string
            cookie_str = config.get('cookie', '').strip()
            if not cookie_str:
                logger.error("Cookie not configured")
                return

            # Convert cookie string to dictionary
            cookie_dict = {}
            for item in cookie_str.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookie_dict[key.strip()] = value.strip()

            # Update session cookies
            self.session.cookies.update(cookie_dict)
            logger.info("Cookie loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {str(e)}")

    async def _get_session(self) -> RetryClient:
        """
        Get a session with retry capability
        
        Returns:
            RetryClient: A session client with configured retry mechanism
        """
        session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=self.headers,
            cookies=self.session.cookies.get_dict()
        )
        retry_client = RetryClient(
            client_session=session,
            retry_options=self.retry_options
        )
        return retry_client

    async def get_wbi_keys(self) -> str:
        """
        Asynchronously fetch WBI keys from Bilibili API
        
        Returns:
            str: Concatenated img_key and sub_key for WBI signature
        
        Raises:
            ValueError: If API returns error
            Exception: For other errors during key retrieval
        """
        async with await self._get_session() as session:
            try:
                async with session.get('https://api.bilibili.com/x/web-interface/nav') as resp:
                    json_content = await resp.json()
                    if json_content.get('code') != 0:
                        raise ValueError(f"API error: {json_content.get('message')}")
                    
                    img_url = json_content['data']['wbi_img']['img_url']
                    sub_url = json_content['data']['wbi_img']['sub_url']
                    
                    img_key = img_url.split('/')[-1].split('.')[0]
                    sub_key = sub_url.split('/')[-1].split('.')[0]
                    
                    return img_key + sub_key
            except Exception as e:
                logger.error(f"Failed to get wbi keys: {str(e)}")
                raise

    async def generate_wbi_params(self) -> dict:
        """
        Generate WBI signature parameters
        
        Creates a signature for API requests using Bilibili's WBI mechanism.
        Includes timestamp and other required parameters.
        
        Returns:
            dict: Parameters including the generated signature
        """
        key = await self.get_wbi_keys()
        
        # Ensure key length is sufficient
        if len(key) < 64:
            logger.warning(f"Key length insufficient: {len(key)}, using default key")
            raise
        
        # Generate mixin key using table
        mixin_key = ''
        for i in self.MIXIN_KEY_TABLE[:32]:
            if i < len(key):
                mixin_key += key[i]
            else:
                logger.error(f"Index {i} out of range for key length {len(key)}")
                break
        
        params = {
            'isGaiaAvoided': 'false',
            'wts': str(int(time.time()))
        }
        
        # Sort and encode parameters
        params_str = urlencode(sorted(params.items()))
        
        # Calculate w_rid
        params['w_rid'] = hashlib.md5(
            (params_str + mixin_key).encode()
        ).hexdigest()
        
        return params

    def resolve_short_url(self, url: str) -> str:
        """
        Resolve short URL to full URL
        
        Args:
            url (str): Short or full Bilibili URL
            
        Returns:
            str: Full URL after resolution
        """
        try:
            response = self.session.get(
                url, 
                headers=self.headers, 
                allow_redirects=False
            )
            if response.status_code == 302:
                return response.headers['Location']
            return url
        except Exception as e:
            logger.error(f"Failed to resolve short URL: {str(e)}")
            return url

    def extract_bvid(self, url: str) -> str:
        """
        Extract BV ID from URL
        
        Args:
            url (str): Bilibili video URL
            
        Returns:
            str: BV ID of the video
            
        Raises:
            ValueError: If URL format is invalid
        """
        full_url = self.resolve_short_url(url)
        if match := re.search(r'BV\w+', full_url):
            return match.group()
        raise ValueError("Invalid Bilibili URL")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def get_video_info(self, bvid: str) -> dict:
        """
        Get video information from Bilibili API
        
        Args:
            bvid (str): BV ID of the video
            
        Returns:
            dict: Video information from API
            
        Raises:
            ValueError: If API returns error
            Exception: For other errors during API request
        """
        api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
        logger.info(f"Fetching video info URL: {api_url}")
        try:
            response = self.session.get(
                api_url,
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            if data['code'] != 0:
                raise ValueError(f"API error: {data['message']}")
            return data
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            raise

    async def download_subtitle(self, url: str) -> None:
        """
        Asynchronously download subtitles for a video
        
        Downloads all available subtitles for a video, including multiple parts if present.
        Creates a directory named after the BV ID and saves subtitles there.
        
        Args:
            url (str): Bilibili video URL
            
        Raises:
            Exception: If download fails for any reason
        """
        try:
            bvid = self.extract_bvid(url)
            sub_dir = bvid
            
            if not os.path.exists(sub_dir):
                os.makedirs(sub_dir, exist_ok=True)

            async with await self._get_session() as session:
                # Get video information
                async with session.get(f'https://www.bilibili.com/video/{bvid}/') as resp:
                    text = await resp.text()
                    aid = text[text.find('"aid"') + 6:]
                    aid = aid[:aid.find(',')]

                # Get part information
                cid_url = f"http://api.bilibili.com/x/player/pagelist?bvid={bvid}"
                async with session.get(cid_url) as resp:
                    cid_json = await resp.json()
                    
                    tasks = []
                    for item in cid_json['data']:
                        task = self._download_part_subtitle(
                            session, 
                            item['cid'], 
                            aid, 
                            item['part'], 
                            sub_dir
                        )
                        tasks.append(task)
                    
                    await asyncio.gather(*tasks)
                    
        except Exception as e:
            logger.error(f"Failed to download subtitle: {str(e)}")
            raise

    async def _download_part_subtitle(
        self, 
        session: RetryClient, 
        cid: int, 
        aid: int, 
        part: str,
        sub_dir: str
    ) -> None:
        """
        Download subtitle for a single video part
        
        Args:
            session (RetryClient): Aiohttp session with retry capability
            cid (int): Part CID
            aid (int): Video AID
            part (str): Part name
            sub_dir (str): Directory to save subtitles
            
        Raises:
            Exception: If download fails
        """
        try:
            wbi_params = await self.generate_wbi_params()
            params = {
                'aid': aid,
                'cid': cid,
                **wbi_params
            }
            
            subtitle_api_url = 'https://api.bilibili.com/x/player/wbi/v2'
            async with session.get(subtitle_api_url, params=params) as resp:
                data = await resp.json()
                subtitle_links = data['data']["subtitle"]['subtitles']
                
                if subtitle_links:
                    subtitle_url = "https:" + subtitle_links[0]['subtitle_url']
                    async with session.get(subtitle_url) as sub_resp:
                        content = await sub_resp.text()
                        
                    file_path = os.path.join(sub_dir, f"{part}.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Downloaded subtitle: {part}")
                else:
                    logger.warning(f"No subtitle found for: {part}")
                    
        except Exception as e:
            logger.error(f"Failed to download part subtitle: {str(e)}")
            raise

def convert_json_to_srt(json_files_path: str):
    """
    Convert JSON format subtitles to SRT format
    
    Args:
        json_files_path (str): Path to directory containing JSON subtitle files
        
    Creates a 'srt' subdirectory and saves converted files there.
    Maintains original JSON files.
    
    Raises:
        Exception: If conversion fails
    """
    try:
        json_files = os.listdir(json_files_path)
        srt_files_path = os.path.join(json_files_path, 'srt')
        if not os.path.exists(srt_files_path):
            os.mkdir(srt_files_path)

        for json_file in json_files:
            if not json_file.endswith('.json'):
                continue
                
            file_name = json_file.replace('.json', '.srt')
            file = ''
            i = 1
            
            with open(os.path.join(json_files_path, json_file), encoding='utf-8') as f:
                datas = json.load(f)

            for data in datas['body']:
                start = data['from']
                stop = data['to']
                content = data['content']
                file += f'{i}\n'
                
                # Process timestamp format
                for t in (start, stop):
                    hour = math.floor(t) // 3600
                    minute = (math.floor(t) - hour * 3600) // 60
                    sec = math.floor(t) - hour * 3600 - minute * 60
                    minisec = int(math.modf(t)[0] * 100)
                    file += f'{hour:02d}:{minute:02d}:{sec:02d},{minisec:02d}'
                    if t == start:
                        file += ' --> '
                
                file += f'\n{content}\n\n'
                i += 1

            with open(os.path.join(srt_files_path, file_name), 'w', encoding='utf-8') as f:
                f.write(file)
            logger.info(f"Converted to SRT: {file_name}")
            
    except Exception as e:
        logger.error(f"Failed to convert to SRT: {str(e)}")
        raise

def setup_logging():
    """
    Configure logging settings
    
    Sets up logging with both file and console output.
    Log level is set to INFO by default.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bilibili_subtitle.log'),
            logging.StreamHandler()
        ]
    )

if __name__ == '__main__':
    setup_logging()
    
    # Check and create config file if not exists
    if not os.path.exists('config.json'):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump({"cookie": ""}, f, indent=4)
        print("Please configure your cookie in config.json")
        exit(1)
    
    # Add multiple video URLs here
    urls = [
        # "https://b23.tv/xxxxxx",  # Example of short URL
        # "https://www.bilibili.com/video/BVxxxxxx",  # Example of full URL
    ]
    
    async def main():
        spider = BilibiliSubtitle()
        
        # Limit concurrent downloads to 3
        semaphore = asyncio.Semaphore(3)
        
        async def download_with_limit(url):
            async with semaphore:
                return await spider.download_subtitle(url)
        
        tasks = [download_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and convert to SRT
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process {url}: {result}")
            else:
                bvid = spider.extract_bvid(url)
                convert_json_to_srt(f'./{bvid}')
    
    # Run async main function
    asyncio.run(main())