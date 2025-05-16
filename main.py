import os
import time
import random
import aiohttp
import asyncio
import requests
from web3 import Web3
from eth_account.messages import encode_defunct
from eth_account import Account
from datetime import datetime

LOGIN_URL = 'https://api.pharosnetwork.xyz/user/login'
FAUCET_URL = 'https://api.pharosnetwork.xyz/faucet/daily?address='
CHECKIN_URL = 'https://api.pharosnetwork.xyz/sign/in?address='
API_URL = 'https://api.pharosnetwork.xyz'
MESSAGE = 'pharos'
RPC_URL = 'https://testnet.dplabs-internal.com'
CHAIN_ID = 688688
VERIFY_TASK_ID_SEND = 103
DELAY_BETWEEN_TX = 5

ENABLE_FAUCET = True
ENABLE_CHECKIN = True
ENABLE_TRANSACTION = True
COLOR_RESET = '\033[0m'
COLOR_GREEN = '\033[32m'
COLOR_RED = '\033[31m'
COLOR_YELLOW = '\033[33m'
COLOR_BLUE = '\033[34m'
COLOR_CYAN = '\033[36m'
COLOR_MAGENTA = '\033[35m'
COLOR_PURPLE = '\033[35m'
COLOR_WHITE = '\033[37m'
COLOR_BOLD = '\033[1m'

def print_logo():

    os.system('clear' if os.name == 'posix' else 'cls')
    
    print("")
    print(f"{COLOR_CYAN}+--------------------------------------------------+{COLOR_RESET}")
    print(f"{COLOR_CYAN}|                                                  |{COLOR_RESET}")
    print(f"{COLOR_BLUE}|     BANG PATENG - PHAROS NETWORK TESTNET TOOL    |{COLOR_RESET}")
    print(f"{COLOR_CYAN}|                                                  |{COLOR_RESET}")
    print(f"{COLOR_CYAN}+--------------------------------------------------+{COLOR_RESET}")
    print("")
    print(f"{COLOR_PURPLE}+------------------ CONTACT INFO -------------------+{COLOR_RESET}")
    print(f"{COLOR_GREEN}|                                                  |{COLOR_RESET}")
    print(f"{COLOR_GREEN}|  Telegram       : @bangpateng_airdrop            |{COLOR_RESET}")
    print(f"{COLOR_GREEN}|  Website        : https://bangpateng.xyz         |{COLOR_RESET}")
    print(f"{COLOR_GREEN}|                                                  |{COLOR_RESET}")
    print(f"{COLOR_PURPLE}+--------------------------------------------------+{COLOR_RESET}")
    print("")

async def delay(ms):
    await asyncio.sleep(ms / 1000)

def get_timestamp():
    now = datetime.now()
    return f"[{now.strftime('%H:%M:%S')}]"

def load_addresses_from_file(filename="alamat.txt"):
    try:
        with open(filename, 'r') as file:
            addresses = [line.strip() for line in file if line.strip()]
        print(f"{get_timestamp()} {COLOR_GREEN}Berhasil memuat {len(addresses)} alamat dari {filename}{COLOR_RESET}")
        return addresses
    except FileNotFoundError:
        print(f"{get_timestamp()} {COLOR_RED}Error: File {filename} tidak ditemukan!{COLOR_RESET}")
        return []

async def pharos_login(session, address, signature):

    login_url = f"{LOGIN_URL}?address={address}&signature={signature}&invite_code=eTxumDYUuAbqh218"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'authorization': 'Bearer null',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'Referer': 'https://testnet.pharosnetwork.xyz/'
    }
    
    print(f"{get_timestamp()} {COLOR_YELLOW}Login ke Pharos Network...{COLOR_RESET}")
    
    try:
        async with session.post(login_url, headers=headers) as login_res:
            login_data = await login_res.json()
            if login_data and 'data' in login_data and 'jwt' in login_data['data']:
                jwt = login_data['data']['jwt']
                print(f"{get_timestamp()} {COLOR_GREEN}Login berhasil!{COLOR_RESET}")
                return jwt, True
            else:
                print(f"{get_timestamp()} {COLOR_RED}Login: response missing jwt {login_data}{COLOR_RESET}")
                return None, False
    except Exception as e:
        print(f"{get_timestamp()} {COLOR_RED}Error saat login: {str(e)}{COLOR_RESET}")
        return None, False

def verify_transaction(address, jwt, task_id, tx_hash):
    url = f"{API_URL}/task/verify?address={address}&task_id={task_id}&tx_hash={tx_hash}"
    headers = {
        'Authorization': f'Bearer {jwt}',
        'Origin': 'https://testnet.pharosnetwork.xyz',
        'Referer': 'https://testnet.pharosnetwork.xyz/'
    }
    return requests.post(url, headers=headers).json()

def get_profile_info(address, jwt):
    url = f"{API_URL}/user/profile?address={address}"
    headers = {
        'Authorization': f'Bearer {jwt}',
        'Origin': 'https://testnet.pharosnetwork.xyz',
        'Referer': 'https://testnet.pharosnetwork.xyz/'
    }
    return requests.get(url, headers=headers).json()

def send_transaction(w3, from_address, private_key, to_address, value=0.001):
    try:
        to_address = w3.to_checksum_address(to_address)
        
        value_wei = w3.to_wei(value, 'ether')
        nonce = w3.eth.get_transaction_count(from_address)
        
        gas_price = w3.eth.gas_price
        gas_price = int(gas_price * 1.1)
        
        tx = {
            'chainId': CHAIN_ID,
            'from': from_address,
            'to': to_address,
            'value': value_wei,
            'gas': 21000, 
            'gasPrice': gas_price,
            'nonce': nonce,
        }
        
        try:
            estimated_gas = w3.eth.estimate_gas(tx)
            tx['gas'] = estimated_gas
        except Exception as e:
            print(f"{get_timestamp()} {COLOR_YELLOW}Gas estimation failed, using default: {e}{COLOR_RESET}")

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"{get_timestamp()} {COLOR_YELLOW}Transaction sent! Waiting for confirmation...{COLOR_RESET}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"{get_timestamp()} {COLOR_GREEN}Transaction confirmed in block {receipt['blockNumber']}{COLOR_RESET}")
        
        return tx_hash.hex()
    except Exception as e:
        print(f"{get_timestamp()} {COLOR_RED}Error in send_transaction: {str(e)}{COLOR_RESET}")
        raise

async def main():
    global ENABLE_TRANSACTION
    
    print_logo()
    
    print(f"{get_timestamp()} Memulai script...")
    
    priv_keys = []
    try:
        with open('key.txt', 'r', encoding='utf-8') as f:
            priv_keys = [line.strip() for line in f if line.strip()]
        print(f"{get_timestamp()} {COLOR_GREEN}Telah membaca key.txt, jumlah wallet: {len(priv_keys)}{COLOR_RESET}")
    except Exception as e:
        print(f"{get_timestamp()} {COLOR_RED}Error membaca key.txt: {str(e)}{COLOR_RESET}")
        priv_keys = []
    
    if len(priv_keys) == 0:
        print(f"{get_timestamp()} {COLOR_RED}Tidak menemukan private key di file key.txt!{COLOR_RESET}")
        return
    
    recipient_addresses = []
    if ENABLE_TRANSACTION:
        recipient_addresses = load_addresses_from_file("alamat.txt")
        if not recipient_addresses:
            print(f"{get_timestamp()} {COLOR_YELLOW}Transaction feature diaktifkan tetapi tidak ada alamat penerima. Transaksi akan dikirim ke diri sendiri.{COLOR_RESET}")
    
    w3 = None
    if ENABLE_TRANSACTION:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            print(f"{get_timestamp()} {COLOR_RED}Error: Cannot connect to RPC endpoint {RPC_URL}{COLOR_RESET}")
            print(f"{get_timestamp()} {COLOR_YELLOW}Menonaktifkan fitur transaksi.{COLOR_RESET}")
            ENABLE_TRANSACTION = False
        else:
            print(f"{get_timestamp()} {COLOR_GREEN}Connected to network. Chain ID: {w3.eth.chain_id}{COLOR_RESET}")
    
    for i, priv_key in enumerate(priv_keys):
        index = i + 1
        
        address = None
        signature = None
        jwt = None
        
        try:
            account = Account.from_key(priv_key)
            address = account.address
            
            message = encode_defunct(text=MESSAGE)
            signature = Account.sign_message(message, priv_key).signature.hex()
            
            print(f"\n{COLOR_BOLD}Wallet {index}/{len(priv_keys)}: {address}{COLOR_RESET}")
            print(f"{get_timestamp()} {COLOR_GREEN}Telah membuat wallet dan menandatangani pesan{COLOR_RESET}")
            
            if ENABLE_TRANSACTION and w3:
                balance = w3.eth.get_balance(address)
                print(f"{get_timestamp()} {COLOR_GREEN}Account balance: {w3.from_wei(balance, 'ether')} ETH{COLOR_RESET}")
            
        except Exception as e:
            print(f"{get_timestamp()} {COLOR_RED}Invalid private key pada baris {index}: {priv_key}{COLOR_RESET}")
            continue
        
        async with aiohttp.ClientSession() as session:
            jwt, login_ok = await pharos_login(session, address, signature)
            
            if ENABLE_FAUCET and login_ok:
                print(f"{get_timestamp()} {COLOR_YELLOW}Mengklaim faucet harian...{COLOR_RESET}")
                faucet_url = FAUCET_URL + address
                faucet_headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'authorization': f'Bearer {jwt}',
                    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'Referer': 'https://testnet.pharosnetwork.xyz/'
                }
                
                try:
                    async with session.post(faucet_url, headers=faucet_headers) as faucet_res:
                        faucet_data = await faucet_res.json()
                        if faucet_data:
                            if isinstance(faucet_data, dict) and 'msg' in faucet_data:
                                print(f"{get_timestamp()} {COLOR_GREEN}Faucet: {faucet_data['msg']}{COLOR_RESET}")
                            else:
                                print(f"{get_timestamp()} {COLOR_GREEN}Faucet: {faucet_data}{COLOR_RESET}")
                        else:
                            print(f"{get_timestamp()} {COLOR_RED}Faucet: No response data{COLOR_RESET}")
                except Exception as e:
                    print(f"{get_timestamp()} {COLOR_RED}Faucet error: {str(e)}{COLOR_RESET}")
            
            if ENABLE_CHECKIN and login_ok:
                print(f"{get_timestamp()} {COLOR_YELLOW}Melakukan check-in harian...{COLOR_RESET}")
                checkin_url = f"{CHECKIN_URL}{address}"
                checkin_headers = {
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                    'authorization': f'Bearer {jwt}',
                    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-site',
                    'Referer': 'https://testnet.pharosnetwork.xyz/'
                }
                
                try:
                    async with session.post(checkin_url, headers=checkin_headers) as checkin_res:
                        checkin_data = await checkin_res.json()
                        if checkin_data:
                            if isinstance(checkin_data, dict) and 'msg' in checkin_data:
                                print(f"{get_timestamp()} {COLOR_GREEN}Check-in: {checkin_data['msg']}{COLOR_RESET}")
                            else:
                                print(f"{get_timestamp()} {COLOR_GREEN}Check-in: {checkin_data}{COLOR_RESET}")
                        else:
                            print(f"{get_timestamp()} {COLOR_RED}Check-in: No response data{COLOR_RESET}")
                except Exception as e:
                    print(f"{get_timestamp()} {COLOR_RED}Check-in error: {str(e)}{COLOR_RESET}")
        
        if ENABLE_TRANSACTION and login_ok and w3 and jwt:
            print(f"{get_timestamp()} {COLOR_YELLOW}Memulai proses transaksi...{COLOR_RESET}")
            
            num_transactions = 0
            if recipient_addresses:
                while True:
                    try:
                        num_input = input(f"{COLOR_BOLD}Masukkan jumlah transaksi untuk wallet ini (max {len(recipient_addresses)}): {COLOR_RESET}")
                        num_transactions = int(num_input)
                        if 0 < num_transactions <= len(recipient_addresses):
                            break
                        print(f"{COLOR_RED}Masukkan jumlah transaksi antara 1 dan {len(recipient_addresses)}{COLOR_RESET}")
                    except ValueError:
                        print(f"{COLOR_RED}Masukkan angka yang valid!{COLOR_RESET}")
            else:
                while True:
                    try:
                        num_input = input(f"{COLOR_YELLOW}Masukkan jumlah transaksi (akan dikirim ke diri sendiri): {COLOR_RESET}")
                        num_transactions = int(num_input)
                        if num_transactions > 0:
                            break
                        print(f"{COLOR_RED}Masukkan angka lebih besar dari 0!{COLOR_RESET}")
                    except ValueError:
                        print(f"{COLOR_RED}Masukkan angka yang valid!{COLOR_RESET}")
            
            successful_tx = 0
            
            for tx_index in range(1, num_transactions + 1):
                try:
                    print(f"\n{get_timestamp()} {COLOR_YELLOW}Transaksi ke-{tx_index}/{num_transactions}{COLOR_RESET}")

                    if recipient_addresses:
                        to_address = recipient_addresses[(tx_index - 1) % len(recipient_addresses)]
                    else:
                        to_address = address
                    
                    print(f"{get_timestamp()} {COLOR_YELLOW}Alamat tujuan: {to_address}{COLOR_RESET}")
                    
                    print(f"{get_timestamp()} {COLOR_YELLOW}Mengirim transaksi...{COLOR_RESET}")
                    tx_hash = send_transaction(w3, address, priv_key, to_address)
                    print(f"{get_timestamp()} {COLOR_GREEN}Transaksi berhasil! Hash: {tx_hash}{COLOR_RESET}")
                    
                    print(f"{get_timestamp()} {COLOR_YELLOW}Verifikasi transaksi ke server...{COLOR_RESET}")
                    verification = verify_transaction(address, jwt, VERIFY_TASK_ID_SEND, tx_hash)
                    if verification.get('code') == 0 and verification.get('data', {}).get('verified'):
                        print(f"{get_timestamp()} {COLOR_GREEN}Verifikasi berhasil!{COLOR_RESET}")
                        successful_tx += 1
                    else:
                        print(f"{get_timestamp()} {COLOR_RED}Verifikasi gagal.{COLOR_RESET}")
                        print(f"{get_timestamp()} {COLOR_RED}Response: {verification}{COLOR_RESET}")
                    
                    profile = get_profile_info(address, jwt)
                    points = profile.get('data', {}).get('user_info', {}).get('TaskPoints', 0)
                    print(f"{get_timestamp()} {COLOR_GREEN}Total Poin: {points}{COLOR_RESET}")
                    
                    if tx_index < num_transactions:
                        print(f"{get_timestamp()} {COLOR_YELLOW}Menunggu {DELAY_BETWEEN_TX} detik...{COLOR_RESET}")
                        time.sleep(DELAY_BETWEEN_TX)
                
                except Exception as e:
                    print(f"{get_timestamp()} {COLOR_RED}Error terjadi: {str(e)}{COLOR_RESET}")
                    print(f"{get_timestamp()} {COLOR_YELLOW}Menunggu 5 detik sebelum mencoba lagi...{COLOR_RESET}")
                    time.sleep(5)
            
            print(f"\n{get_timestamp()} {COLOR_GREEN}Selesai! {successful_tx} dari {num_transactions} transaksi berhasil diverifikasi.{COLOR_RESET}")
        
        if i < len(priv_keys) - 1:
            random_delay = random.randint(5000, 10000)
            delay_seconds = round(random_delay / 1000)
            print(f"{get_timestamp()} {COLOR_YELLOW}Menunggu {delay_seconds} detik sebelum wallet berikutnya...{COLOR_RESET}")
            await delay(random_delay)

async def zenith_faucet():
    print_logo()
    
    print(f"{get_timestamp()} Memulai script ZenithSwap faucet...")
    
    API_URL = 'https://testnet-router.zenithswap.xyz/api/v1/faucet'
    TOKEN_ADDRESS = '0xAD902CF99C2dE2f1Ba5ec4D642Fd7E49cae9EE37'
    
    priv_keys = []
    try:
        with open('key.txt', 'r', encoding='utf-8') as f:
            priv_keys = [line.strip() for line in f if line.strip()]
        print(f"{get_timestamp()} {COLOR_GREEN}Telah membaca key.txt, jumlah wallet: {len(priv_keys)}{COLOR_RESET}")
    except Exception as e:
        print(f"{get_timestamp()} {COLOR_RED}Error membaca key.txt: {str(e)}{COLOR_RESET}")
        priv_keys = []
    
    if len(priv_keys) == 0:
        print(f"{get_timestamp()} {COLOR_RED}Tidak menemukan private key di file key.txt!{COLOR_RESET}")
        return
    
    async with aiohttp.ClientSession() as session:
        for i, priv_key in enumerate(priv_keys):
            index = i + 1
            
            try:
                account = Account.from_key(priv_key)
                address = account.address
                
                print(f"\n{COLOR_BOLD}Wallet {index}/{len(priv_keys)}: {address} {COLOR_RESET}")
                
            except Exception as e:
                print(f"{get_timestamp()} {COLOR_RED}Invalid private key pada baris {index}: {priv_key}{COLOR_RESET}")
                continue
            
            retry = 0
            while True:
                try:
                    print(f"{get_timestamp()} {COLOR_YELLOW}Mengklaim token dari ZenithSwap faucet...{COLOR_RESET}")
                    
                    headers = {
                        'accept': '*/*',
                        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
                        'content-type': 'application/json',
                        'priority': 'u=1, i',
                        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                        'sec-fetch-dest': 'empty',
                        'sec-fetch-mode': 'cors',
                        'sec-fetch-site': 'same-site',
                        'Referer': 'https://testnet.zenithswap.xyz/'
                    }
                    
                    data = {
                        'tokenAddress': TOKEN_ADDRESS,
                        'userAddress': address
                    }
                    
                    async with session.post(API_URL, json=data, headers=headers) as res:
                        res_data = await res.json()
                        
                        if res_data and res_data.get('status') == 400 and res_data.get('message') == 'system error':
                            retry += 1
                            if retry > 5:
                                print(f"{get_timestamp()} {COLOR_RED}System error, exceeded max retries (5){COLOR_RESET}")
                                break
                            print(f"{get_timestamp()} {COLOR_YELLOW}System error, retrying ({retry}/5)...{COLOR_RESET}")
                            await delay(2000)
                            continue
                        
                        if res_data and 'msg' in res_data:
                            retry_info = f" (retries: {retry})" if retry > 0 else ""
                            print(f"{get_timestamp()} {COLOR_GREEN}{res_data['msg']}{retry_info}{COLOR_RESET}")
                        else:
                            retry_info = f" (retries: {retry})" if retry > 0 else ""
                            print(f"{get_timestamp()} {COLOR_GREEN}{res_data}{retry_info}{COLOR_RESET}")
                        break
                        
                except Exception as e:
                    print(f"{get_timestamp()} {COLOR_RED}Error: {str(e)}{COLOR_RESET}")
                    break
            
            if i < len(priv_keys) - 1:
                print(f"{get_timestamp()} {COLOR_YELLOW}Menunggu 5 detik sebelum wallet berikutnya...{COLOR_RESET}")
                await delay(5000)

def display_menu():
    print_logo()
    
    print(f"\n")
    print(f"{COLOR_CYAN}1. {COLOR_RESET}Pharos Network All-in-One (Faucet, Check-in & Transactions)")
    print(f"{COLOR_MAGENTA}2. {COLOR_RESET}ZenithSwap Faucet")
    print(f"{COLOR_YELLOW}3. {COLOR_RESET}Jalankan Kedua Script")
    print(f"{COLOR_RED}0. {COLOR_RESET}Keluar")
    print(f"\n")

async def run_both():
    await main()
    print("\n{COLOR_YELLOW}Menjalankan script berikutnya")
    await asyncio.sleep(3)
    await zenith_faucet()

if __name__ == "__main__":
    try:
        display_menu()
        choice = input(f"{COLOR_BOLD}Pilihan Anda > {COLOR_RESET}")
        
        if choice == "1":
            asyncio.run(main())
            print("\nPharos Network All-in-One selesai!")
        elif choice == "2":
            asyncio.run(zenith_faucet())
            print("\nZenithSwap Faucet selesai!")
        elif choice == "3":
            asyncio.run(run_both())
            print("\nKedua script telah selesai dijalankan!")
        elif choice == "0":
            print("\nKeluar dari program...")
        else:
            print("\nPilihan tidak valid!")
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan oleh pengguna.")
    except Exception as e:
        print(f"\nError: {str(e)}")
