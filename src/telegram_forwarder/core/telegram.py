from pyrogram import (Client,errors)
import os, random, asyncio, aiohttp, json, re
import psutil
from .paths import PROJECT_ROOT, DATA_DIR, ACCOUNT_DIR, PROXY_FILE, ENV_FILE


def load_env(path=None):
    """Carrega variaveis de um arquivo .env para o ambiente.
    Nao sobrescreve variaveis que ja existem no ambiente."""
    if path is None:
        path = str(ENV_FILE)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        pass


load_env()


class telegram_panel:
    
    @staticmethod
    def list_accounts():
        ls = set([i.name.replace('.session', '') for i in os.scandir(str(ACCOUNT_DIR)) if i.name.endswith('.session')])
        js = set([i.name.replace('.json', '') for i in os.scandir(str(DATA_DIR)) if i.name.endswith('.json')])
        return list(ls.intersection(js))
    
    
    @staticmethod
    async def check_proxy_req(ip, port, username, password, timeout=5):
        proxy = f'socks5://{username}:{password}@{ip}:{port}'
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://core.telegram.org/bots', proxy=proxy, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        print(f'Proxy {ip} is valid.')
                        return True
                    else:
                        print(f'Proxy {ip} returned status code {response.status}.')
                        return False
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f'Proxy {ip} is invalid: {e}')
            return False
    
    
    @staticmethod
    def read_proxies_from_file():
        try:
            with open(str(PROXY_FILE), 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file if line.strip()]
            # Mantém apenas linhas no formato valido ip:porta:usuario:senha
            valid = []
            for line in lines:
                parts = line.split(':')
                if len(parts) == 4 and parts[1].isdigit():
                    valid.append(line)
                else:
                    print(f"Ignoring invalid proxy line: {line}")
            return valid
        except Exception as e:
            print(f"Error reading proxy file: {e}")
            return []
    
    
    @staticmethod
    def build_proxy(info):
        return {
            "scheme": "socks5",
            "hostname": info[0],
            "port": int(info[1]),
            "username": info[2],
            "password": info[3]
        }


    @staticmethod
    async def get_proxy(ip=None):
        async def is_valid(proxy_info):
            return await telegram_panel.check_proxy_req(proxy_info[0], int(proxy_info[1]), proxy_info[2], proxy_info[3])

        if ip:
            proxy_info = telegram_panel.get_proxy_by_ip(ip)
            if proxy_info and await is_valid(proxy_info):
                return telegram_panel.build_proxy(proxy_info), True

        for _ in range(random.randint(5, 15)):
            proxy_info = telegram_panel.get_random_proxy()
            if proxy_info is None:
                break
            if await is_valid(proxy_info):
                return telegram_panel.build_proxy(proxy_info), False
        # Sem proxies validos: conexao direta (sem proxy)
        print("No valid proxies found. Using direct connection.")
        return None, False

    
    @staticmethod
    def get_proxy_by_ip(ip):
        proxies = telegram_panel.read_proxies_from_file()
        if not proxies:
            return None
        for proxy in proxies:
            if ip in proxy:
                return proxy.split(':')
        return random.choice(proxies).split(':')

    
    @staticmethod
    def get_random_proxy():
        proxies = telegram_panel.read_proxies_from_file()
        if not proxies:
            return None
        return random.choice(proxies).split(':')


    @staticmethod
    def get_api_credentials():
        """Le as credenciais da API das variaveis de ambiente API_ID e API_HASH
        (carregadas do arquivo .env se existir)."""
        api_id = os.environ.get('API_ID', '').strip()
        api_hash = os.environ.get('API_HASH', '').strip()
        if not api_id or not api_hash:
            raise ValueError(
                "API_ID/API_HASH not configured. "
                "Fill the .env file (see .env.example) with your credentials from https://my.telegram.org/apps"
            )
        if not api_id.isdigit():
            raise ValueError(
                "Invalid API_ID: it must be a number. Check the .env file."
            )
        return int(api_id), api_hash
    
    
    @staticmethod
    async def add_account(phone :str) -> dict:
        if phone in telegram_panel.list_accounts():
            return {
                'status':False,
                'message':'Account {} already exist'.format(phone)
            }
        
        try:
            api_id, api_hash = telegram_panel.get_api_credentials()
        except ValueError as e:
            return {'status': False, 'message': str(e)}
        proxy = await telegram_panel.get_proxy()
        cli = Client(str(ACCOUNT_DIR / phone), api_id, api_hash, proxy=proxy[0])
        try:
            await cli.connect()
            result = await cli.send_code(phone)
            return {
                'status':True,
                'cli':cli,
                "phone":phone,
                "code_hash":result.phone_code_hash,
                "api_id":api_id,
                "api_hash":api_hash,
                "proxy":proxy[0]["hostname"] if proxy[0] else ""
                
            }
        except Exception as e:
            try:await cli.disconnect()
            except:pass
            try:os.remove(str(ACCOUNT_DIR / '{}.session'.format(phone)))
            except:pass
            return {
                'status':False,
                'message':str(e)
            }
    
    
    @staticmethod
    async def get_code(cli : Client , phone : str, code_hash : str , code : str )-> dict:
        try:
            await cli.sign_in(phone, code_hash ,code)
            info = await cli.get_me()
            print("Account :",phone ,"Name :",info.first_name, "Account ID :",info.id, "Successfully logged in")
            await cli.disconnect()
            return {
                'status':True,
                'message':'Successfully logged in : {}'.format(phone)
            }
        except errors.PhoneCodeInvalid:
            return {
                'status':False,
                'message':'invalid_code'
            }
        except errors.SessionPasswordNeeded:
            return {
                'status':False,
                'message':'FA2'
            }
        except Exception as e:
            try:await cli.disconnect()
            except:pass
            try:os.remove(str(ACCOUNT_DIR / '{}.session'.format(phone)))
            except:pass
            return {
                'status':False,
                'message':str(e)
            }
    
    
    @staticmethod
    async def get_password(cli : Client , phone : str, password : str )-> dict:
        try:
            await cli.check_password(password=password)
            info = await cli.get_me()
            print("Account :",phone ,"Name :",info.first_name, "Account ID :",info.id, "Successfully logged in")
            await cli.disconnect()
            return {
                'status':True,
                'message':'Successfully logged in : {}'.format(phone)
            }
        except errors.PasswordHashInvalid:
            return {
                'status':False,
                'message':'invalid_password'
            }
        except Exception as e:
            try:await cli.disconnect()
            except:pass
            try:os.remove(str(ACCOUNT_DIR / '{}.session'.format(phone)))
            except:pass
            return {
                'status':False,
                'message':str(e)
            }
    
    
    @staticmethod
    async def cancel_acc(cli : Client , phone : str) -> None:
        try:await cli.disconnect()
        except:pass
        try:os.remove(str(ACCOUNT_DIR / '{}.session'.format(phone)))
        except:pass
        return
    
    
    @staticmethod
    def make_json_data(phone :str , api_id : int , api_hash : str , proxy : str , fa2 : str)->bool:
        try:
            with open(str(DATA_DIR / '{}.json'.format(phone)), 'w', encoding='utf-8') as file:
                json.dump({'api_id':api_id,'api_hash':api_hash,'proxy':proxy,'fa2':fa2}, file)
            return True
        except Exception as e:
            return False

    
    @staticmethod
    def get_json_data(phone :str)->dict:
        try:
            with open(str(DATA_DIR / '{}.json'.format(phone)), 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            return None
    
    
    @staticmethod
    def save_json_data(phone : str , data : dict)-> bool:
        try:
            with open(str(DATA_DIR / '{}.json'.format(phone)), 'w', encoding='utf-8') as file:
                json.dump(data, file)
            return True
        except Exception as e:
            return False
    
    
    @staticmethod
    def remove_account(phone :str)->bool:
        try:os.remove(str(ACCOUNT_DIR / '{}.session'.format(phone)))
        except:pass
        try:os.remove(str(DATA_DIR / '{}.json'.format(phone)))
        except:pass
        return True
    
    
    @staticmethod
    def list_channel()->list:
        try:
            return [i.name.replace('.json', '') for i in os.scandir(str(PROJECT_ROOT / "masssages")) if i.name.endswith('.json')]
        except Exception as e:
            print(f"Error reading channel file: {e}")
            return []


    @staticmethod
    def is_valid_telegram_link(text):
        pattern_username = r"^@[a-zA-Z0-9_]{5,}$"
        pattern_invite = r"^t\.me/\+[\w\-]{10,}$"
        return bool(re.match(pattern_username, text)) or bool(re.match(pattern_invite, text))

    @staticmethod
    def is_valid_chat_id(text):
        """Valida id numerico de chat (ex: -1001234567890, -123456, 123456)."""
        t = (text or '').strip()
        return bool(t.lstrip('-').isdigit()) and len(t) >= 5


    @staticmethod
    def get_max_concurrent():
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True)

        ram_gb = int(ram_gb + 0.5)

        print("CPU Cores:", cpu_cores)
        print("RAM:", ram_gb, "GB")
        
        if ram_gb <= 2 and cpu_cores <= 2:
            return 3
        elif ram_gb <= 3 and cpu_cores <= 2:
            return 5
        elif ram_gb <= 4 and cpu_cores <= 4:
            return 6
        elif ram_gb <= 6 and cpu_cores <= 4:
            return 8
        else:
            return 10
    
    
    @staticmethod
    async def Join(new : Client, link: str): 
        try:
            result = await new.join_chat(link)
            # Kurigram novo: join_chat retorna ChatJoinResult com .chat dentro
            chat = getattr(result, 'chat', None)
            if chat is not None and getattr(chat, 'id', None) is not None:
                return [chat.id, chat.title, link]
            # Compatibilidade com versoes antigas: retorna Chat diretamente
            if getattr(result, 'id', None) is not None:
                return [result.id, result.title, link]
            # Fallback: busca as informacoes do chat
            infolink = await new.get_chat(link)
            return [infolink.id, infolink.title, link]
        except errors.bad_request_400.UserAlreadyParticipant:
            infolink = await new.get_chat(link)
            return [infolink.id,infolink.title,link]
        except Exception as e :
            return [str(e)]
    
    @staticmethod
    async def get_chat(new : Client, chat_id: int): 
        try:
            infolink = await new.get_chat(chat_id)
            return [infolink.id,infolink.title,str(chat_id)]
        except Exception as e :
            return [str(e)]
        


