import requests
import time
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import re
import threading

from colorama import Fore, Style, init

API_URL = "https://nodewars.nodepay.ai"
HEADER = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, ztsd",
    "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8",
    "Priority": "u=1, i",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Origin": "https://minigame-nw.nodepay.ai",
    "Referer": "https://minigame-nw.nodepay.ai/",
    "Sec-CH-Ua": 'Microsoft Edge";v="131", "Chromium";v="131", "Not_A_Brand";v="24", "Microsoft Edge WebView2";v="131',
    "Sec-CH-Ua-Mobile": "?0",
    "Sec-CH-Ua-Platform": "Windows",
}

def read_proxies_from_file(file_path: str = 'proxies.txt') -> list:
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}Proxy file {file_path} not found! Running without proxies.{Fore.RESET}")
        return []

def extract_username_from_query(query_string: str) -> str:
    try:
        match = re.search(r'username%22%3A%22([^%"]+)', query_string)
        username = match.group(1) if match else query_string[:15]
        
        if len(username) > 15:
            username = username[:15]
        
        elif len(username) < 15:
            padding = 15 - len(username)
            left_pad = padding // 2
            right_pad = padding - left_pad
            username = ' ' * left_pad + username + ' ' * right_pad
        
        return username
    except Exception:
        return ' ' * 15

def setup_logging(username: str) -> logging.Logger:
    logger = logging.getLogger(username)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        f'{Fore.LIGHTWHITE_EX}%(asctime)s{Fore.RESET} - {Fore.CYAN}[{username}]{Fore.RESET} - %(levelname)s: %(message)s', 
        datefmt='[%d-%m-%Y %H:%M:%S]'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def generate_action_logs(base_prefix: str = '10') -> list:
    action_logs = []
    current_timestamp = int(time.time() * 1000000)
    
    possible_prefixes = ['10', '31', '53', '43', '10', '10', '10']
    
    for _ in range(24):
        prefix = random.choice(possible_prefixes)
        unique_number = random.randint(1000, 9999)
        current_timestamp += random.randint(100, 1000)
        action_log = f"{prefix}{unique_number}{current_timestamp}"
        action_logs.append(action_log)
    
    return action_logs

def generate_random_tokens(tokens: list) -> Dict[str, int]:
    return {token: random.randint(1, 3) for token in tokens}

def read_query_strings_from_file(file_path: str = 'queries.txt') -> list:
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}File {file_path} not found!{Fore.RESET}")
        return []

def login_with_query_string(query_string: str, logger: logging.Logger, proxy: str = None) -> Optional[Dict[str, Any]]:
    url = f"{API_URL}/users/profile"
    headers = {**HEADER, "Authorization": f"Bearer {query_string}"}
    
    proxies = {'http': proxy, 'https': proxy} if proxy else {}
    
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        logger.info(f"{Fore.YELLOW}Proxy Used: {proxy or 'Direct Connection'}{Fore.RESET}")
        logger.info(f"{Fore.GREEN}Login successful!{Fore.RESET}")

        return response.json()["data"]
    except requests.exceptions.RequestException as e:
        logger.error(f"{Fore.RED}Login failed: {e}{Fore.RESET}")
        return None

def claim_daily(query_string: str, logger: logging.Logger, proxy: str = None, last_claim: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    if last_claim and datetime.now() - last_claim < timedelta(hours=24):
        logger.info(f"{Fore.YELLOW}Not time for daily claim yet. Wait 24 hours.{Fore.RESET}")
        return None

    url = f"{API_URL}/missions/daily/claim"
    headers = {**HEADER, "Authorization": f"Bearer {query_string}"}
    mission_id = "66c4b006c767c2cee0afe806"
    payload = {"missionId": mission_id}
    
    proxies = {'http': proxy, 'https': proxy} if proxy else {}
    
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            logger.info(f"{Fore.GREEN}Daily claim successful!{Fore.RESET}")
            return response.json()
        elif response.status_code == 400:
            logger.warning(f"{Fore.YELLOW}Daily reward already claimed!{Fore.RESET}")
            return None
        else:
            logger.error(f"{Fore.RED}Unexpected response: {response.status_code}{Fore.RESET}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"{Fore.RED}Daily claim failed: {e}{Fore.RESET}")
        return None

def start_game(level: int, query_string: str, logger: logging.Logger, proxy: str = None) -> Optional[Dict[str, Any]]:
    url = f"{API_URL}/game/start"
    headers = {**HEADER, "Authorization": f"Bearer {query_string}"}
    payload = {"level": level}
    
    proxies = {'http': proxy, 'https': proxy} if proxy else {}
    
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        logger.info(f"{Fore.GREEN}Game started at level {level}!{Fore.RESET}")
        return response.json()["data"]
    except requests.exceptions.RequestException as e:
        logger.error(f"{Fore.RED}Failed to start game: {e}{Fore.RESET}")
        return None

def finish_game(
    session_id: str, 
    game_log_id: str, 
    query_string: str,
    logger: logging.Logger,
    proxy: str = None
) -> Optional[Dict[str, Any]]:
    url = f"{API_URL}/game/finish"
    headers = {**HEADER, "Authorization": f"Bearer {query_string}"}
    
    token_list = [
        "nodewars", "shiba", "nodepay", "pepe", "polkadot", 
        "babydoge", "bnb", "avax", "eth", "usdt", "solana", 
        "aptos", "ton", "bonk", "bomb", "doge", "floki", 
        "chainlink", "uniswap", "trx", "lido", "xrp", "ltc", 
        "ada", "sui", "dogwifhat", "near", "bitcoin"
    ]
    
    collected_tokens = generate_random_tokens(token_list)
    action_logs = generate_action_logs()
    score = random.randint(45, 60)
    time_spent = random.randint(25000, 30000)
    
    payload = {
        "sessionId": session_id,
        "gameLogId": game_log_id,
        "isCompleted": True,
        "timeSpent": time_spent,
        "actionLogs": action_logs,
        "score": score,
        "collectedTokens": collected_tokens
    }
    
    proxies = {'http': proxy, 'https': proxy} if proxy else {}
    
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        response_score = response_data.get('data', {}).get('score', score)
        logger.info(f"{Fore.GREEN}Game completed! {Fore.RESET}{Fore.LIGHTYELLOW_EX}Score: {response_score}{Fore.RESET}")
        token_str = ", ".join([f"{token}: {amount}" for token, amount in collected_tokens.items()])
        logger.info(f"{Fore.CYAN}Tokens collected: {Fore.RESET}{Fore.LIGHTYELLOW_EX}{token_str}{Fore.RESET}")
        
        return response_data
    except requests.exceptions.RequestException as e:
        logger.error(f"{Fore.RED}Failed to complete game: {e}{Fore.RESET}")
        return None

def process_account(query_string: str, proxies: list):
    username = extract_username_from_query(query_string)
    logger = setup_logging(username)
    last_claim_time = None
    delay = random.randint(30, 60)
    
    proxy = random.choice(proxies) if proxies else None
    
    while True:
        try:
            user_data = login_with_query_string(query_string, logger, proxy)
            if not user_data:
                break

            logger.info(f"{Fore.LIGHTMAGENTA_EX}UserID: {user_data.get('userId')}{Fore.RESET}")
            logger.info(f"{Fore.LIGHTMAGENTA_EX}Name: {user_data.get('name')}{Fore.RESET}")
            logger.info(f"{Fore.LIGHTMAGENTA_EX}Level: {user_data.get('level')}{Fore.RESET}")
            logger.info(f"{Fore.LIGHTMAGENTA_EX}Humanity: {user_data.get('humanity')}{Fore.RESET}")
            logger.info(f"{Fore.LIGHTMAGENTA_EX}Points: {user_data.get('points')}{Fore.RESET}")
            logger.info(f"{Fore.LIGHTMAGENTA_EX}Coins: {user_data.get('coins')}{Fore.RESET}")
            
            claim_response = claim_daily(query_string, logger, proxy, last_claim_time)
            if claim_response:
                last_claim_time = datetime.now()
                logger.info(f"{Fore.CYAN}Claim Data: {claim_response}{Fore.RESET}")
            
            while True:
                user_level = user_data.get("level", 1)
                game_data = start_game(user_level, query_string, logger, proxy)
                
                if not game_data:
                    logger.error(f"{Fore.RED}Failed to start game. Stopping loop.{Fore.RESET}")
                    break

                session_id = game_data["sessionId"]
                game_log_id = game_data["gameLogId"]

                logger.info(f"{Fore.BLUE}Game in progress...{Fore.RESET}")
                time.sleep(delay)

                finish_response = finish_game(
                    session_id, 
                    game_log_id, 
                    query_string=query_string,
                    logger=logger,
                    proxy=proxy
                )
                
                if finish_response:
                    if finish_response.get("data", {}).get("isLevelUp"):
                        user_data["level"] += 1
                        logger.info(f"{Fore.GREEN}Leveled Up!{Fore.RESET}")

                    logger.info(f"{Fore.BLUE}Delay {delay} seconds before next game...{Fore.RESET}")
                    time.sleep(delay)

        except Exception as e:
            logger.error(f"{Fore.RED}Error on account: {e}{Fore.RESET}")
            time.sleep(delay) 

def main():
    init(autoreset=True)
    banner = """
   \\  |             |           \\ \\        /                 
    \\ |   _ \\    _` |   _ \\      \\ \\  \\   /  _` |   __|  __| 
  |\\  |  (   |  (   |   __/       \\ \\  \\ /  (   |  |   \\__ \\ 
 _| \\_| \\___/  \\__,_| \\___|        \\_/\\_/  \\__,_| _|   ____/ 
                                                             
                Node Wars Bot - Multi Account
                Part of NodePay Network
                    Github: IM-Hanzou
    """
    print(f'{Fore.LIGHTCYAN_EX}{banner}{Fore.RESET}')
    print(f"{Fore.YELLOW}Starting bot...{Fore.RESET}")
    query_strings = read_query_strings_from_file()
    proxies = read_proxies_from_file()
    
    if not query_strings:
        print(f"{Fore.RED}No query strings found!{Fore.RESET}")
        return

    threads = []
    for query_string in query_strings:
        thread = threading.Thread(target=process_account, args=(query_string, proxies))
        thread.start()
        threads.append(thread)
        time.sleep(5)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
