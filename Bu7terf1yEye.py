import re
import os
import csv
import socket
import threading
import json
from datetime import datetime
import requests

class Alive:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    url_list = []
    thread_count = 10
    scan_lock = threading.Lock()
    result_file = None

    def url_get(self):
        urls = []
        print("请输入要探测的URL，支持多行输入,空行结束：")
        try:
            while True:
                url = input().strip()
                if url == "":
                    break
                if not re.match(r"^https?://", url):
                    url = "https://" + url
                urls.append(url)
            if not urls:
                print("\033[31m[!]未输入任何URL！\033[0m")
                input("按回车继续存活检测...")
                return False
            for u in urls:
                spider = Alive()
                spider.url = u
                spider.code = 0
                spider.length = 0
                spider.title = ""
                self.url_list.append(spider)
        except:
            print("\033[31m[!]输入错误!\033[0m")
            input("按回车继续存活检测...")
            return False

    def file_get(self):
        urls=[]
        file_path=input("请输入文件路径（回车默认targets.txt）：")
        if not file_path:
            file_path = "targets.txt"
        try:
            with open(file_path,'r',encoding='utf-8') as f:
                for line in f:
                    url=line.strip()
                    if not re.match(r"^https?://", url):
                        url = "https://" + url
                    urls.append(url)
            if not urls:
                print("\033[31m[!]文件中未找到任何URL！\033[0m")
                input("按回车继续存活检测...")
                return False
            for u in urls:
                spider=Alive()
                spider.url=u
                spider.code=0
                spider.length=0
                spider.title=""
                self.url_list.append(spider)
        except:
            print("\033[31m[!]文件读取失败！\033[0m")
            input("按回车继续存活检测...")
            return False

    def search(self):
        print("开始探测...")
        current_path = os.getcwd()
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        alive_dir = f"{current_path}\\Alive"
        if not os.path.exists(alive_dir):
            os.makedirs(alive_dir)
        with open(f"{alive_dir}\\{current_time}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(self.result_file)
            writer.writerow(["URL", "状态码", "标题", "响应长度"])
            self.result_file = f
        self.result_file.flush()
        os.fsync(self.result_file.fileno())
        thread_urls = [[] for _ in range(self.thread_count)]
        for i, u in enumerate(self.url_list):
            thread_urls[i % self.thread_count].append(u)
        threads = []
        for urls in thread_urls:
            t = threading.Thread(target=self.scan_url, args=(urls,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.result_file.close()
        if os.path.getsize(f"{alive_dir}\\{current_time}.csv") == 35:
            os.remove(f"{alive_dir}\\{current_time}.csv")
            print("\033[31m[!]没有存活目标！\033[0m")
            input("按回车继续存活检测...")
            return False
        else:
            print(f"\033[32m[*]探测完成！存活目标已保存到{alive_dir}\\{current_time}.csv\033[0m")
        input("按回车继续存活检测...")
    
    def scan_url(self, urls):
        for u in urls:
            try:
                response = requests.get(u.url, headers=self.headers, timeout=2.5)
                u.code = response.status_code
                u.length = len(response.text)
                u.title = re.search(r'<title>(.*?)</title>', response.text)
                if u.title:
                    u.title = u.title.group(1).strip()
                else:
                    u.title = "无标题"
                with self.scan_lock:
                    if u.code != 404:
                        if u.title == "无标题":
                            print(f"\033[33m[*]状态码[\033[32m{u.code}\033[33m] -> 标题[\033[31m{u.title}\033[33m] -> 响应长度[\033[32m{u.length}\033[33m] -> {u.url}\033[0m")
                            self.result_file.write(f"{u.url}, {u.code}, {u.title}, {u.length}\n")
                            self.result_file.flush()
                            os.fsync(self.result_file.fileno())
                        else:
                            print(f"\033[33m[*]状态码[\033[32m{u.code}\033[33m] -> 标题[\033[32m{u.title}\033[33m] -> 响应长度[\033[32m{u.length}\033[33m] -> {u.url}\033[0m")
                            self.result_file.write(f"{u.url}, {u.code}, {u.title}, {u.length}\n")
                            self.result_file.flush()
                            os.fsync(self.result_file.fileno())
                    else:
                        print(f"\033[35m[*]状态码[{u.code}] -> 标题[{u.title}] -> 响应长度[{u.length}] -> {u.url}\033[0m")
            except:
                with self.scan_lock:
                    print(f"\033[31m[!]目标死亡或请求失败 -> {u.url}\033[0m")


    def distinct(self):
        try:
            seen = set()
            new_list = []
            for u in self.url_list:
                if u.url not in seen:
                    seen.add(u.url)
                    new_list.append(u)
            self.url_list = new_list
        except:
            pass

    def clean(self):
        self.url_list = []

    def set_thread_count(self):
        try:
            choice = input("请输入线程数（默认10）：").strip()
            if not choice:
                self.thread_count = 10
            else:
                self.thread_count = int(choice)
            print(f"\033[32m[*]线程数已设置为：{self.thread_count}\033[0m")
            input("按回车继续...")
        except:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续...")

    def menu(self):
        print("\n\033[32m[*]存活检测菜单\033[0m")
        print("======================================================")
        print(f"可选择功能：1.输入探测 2.批量探测 3.设置线程数（当前：{self.thread_count}） 4.返回")
	
class Port:
    target = ""
    port_list = []
    port_scan_list = set()
    scan_lock = threading.Lock()
    open_port_list = set()

    def port_menu(self):
        print("\n\033[32m[*]端口扫描菜单\033[0m")
        print("======================================================")
        print("可选择功能：1.输入IP地址或url 2.返回")

    def target_get(self):
        self.current_path = os.getcwd()
        print("请输入目标IP地址或url：")
        try:
            self.target = input().strip()
            self.target = socket.gethostbyname(self.target.replace("https://", "").replace("http://", ""))
        except:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续端口扫描...")
            return False
        try:
            choice = input("请输入线程数（默认10）：").strip()
            if not choice:
                self.thread_count = 10
            else:
                self.thread_count = int(choice)
        except:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续端口扫描...")
            return False
        print("可选择扫描的端口（默认Top100端口）：1.Top100 2.Top1000")
        try:
            port_choice = input("请输入选项：").strip()
            if not port_choice:
                port_choice = "1"
        except:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续端口扫描...")
            return False
        if port_choice == "1":
            self.port_file = "Top100port.txt"
        elif port_choice == "2":
            self.port_file = "Top1000port.txt"
        else:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续端口扫描...")
            return False
        self.start_scan()

    def port_scan(self, ports):
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((self.target, port))
                s.close()
                with self.scan_lock:
                    print(f"\033[32m[*]端口[{port}]开放\033[0m")
                    self.open_port_list.add(port)
            except:
                with self.scan_lock:
                    print(f"\033[31m[!]端口[{port}]关闭\033[0m")

    def start_scan(self):
        with open(f"{self.current_path}\\Dict\\{self.port_file}", "r", encoding="utf-8") as f:
            port_list = [int(port.strip()) for port in f.read().split(",")]
        thread_ports = [[] for _ in range(self.thread_count)]
        for i, port in enumerate(port_list):
            thread_ports[i % self.thread_count].append(port)
        threads = []
        for ports in thread_ports:
            t = threading.Thread(target=self.port_scan, args=(ports,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        with open(f"{self.current_path}\\Port\\{self.target}.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["端口", "状态"])
            for port in self.open_port_list:
                writer.writerow([port, "开放"])
                f.flush()
                os.fsync(f.fileno())
        print(f"\033[32m[*]扫描完成！结果已保存到{self.current_path}\\Port\\{self.target}.csv\033[0m")
        print(f"\033[32m[*]目标{self.target}开放端口：{self.open_port_list}\033[0m")
        input("按回车继续端口扫描...")

class Subdomain:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    subdomain_list=[]
    url = ""
    thread_count = 10
    scan_lock = threading.Lock()
    result_file = None

    def Subdomain_menu(self):
        print("\n\033[32m[*]子域名枚举菜单\033[0m")
        print("======================================================")
        print("可选择功能：1.输入单个要枚举的子域名目标的URL 2.返回")

    def url_get(self):
        print("请输入要子域名枚举的URL：")
        try:
            self.url = input().strip()
            if not self.url:
                print("\033[31m[!]未输入URL地址！\033[0m")
                input("按回车继续子域名枚举...")
                return False
            self.url = self.url.replace("https://", "").replace("http://", "").replace("www.", "")
            self.current_path = os.getcwd()
            if not re.match(r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$", self.url):
                print("\033[31m[!]输入错误！\033[0m")
                input("按回车继续子域名枚举...")
                return False
        except:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续子域名枚举...")
            return False
        try:
            choice = input("请输入线程数（默认10）：").strip()
            if not choice:
                self.thread_count = 10
            else:
                self.thread_count = int(choice)
        except:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续子域名枚举...")
            return False
        
    def subdomain_scan(self):
        with open(f"{self.current_path}\\Dict\\submin.txt", "r", encoding="utf-8") as f:
            self.subdomain_list = [subdomain.strip() for subdomain in f.readlines()]
        subdomain_dir = f"{self.current_path}\\Subdomain"
        if not os.path.exists(subdomain_dir):
            os.makedirs(subdomain_dir)
        with open(f"{subdomain_dir}\\{self.url}.txt", "w", encoding="utf-8") as f:
            self.result_file = f
        thread_subdomains = [[] for _ in range(self.thread_count)]
        for i, subdomain in enumerate(self.subdomain_list):
            thread_subdomains[i % self.thread_count].append(subdomain)
        threads = []
        for subdomains in thread_subdomains:
            t = threading.Thread(target=self.scan_subdomain, args=(subdomains,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.result_file.close()
        if os.path.getsize(f"{subdomain_dir}\\{self.url}.txt") == 0:
            os.remove(f"{subdomain_dir}\\{self.url}.txt")
            print(f"\033[31m[!]目标{self.url}不存在子域名\033[0m")
            input("按回车继续子域名枚举...")
        else:
            print(f"\033[32m[*]枚举完成！结果已保存到{subdomain_dir}\\{self.url}.txt\033[0m")
            input("按回车继续子域名枚举...")
    
    def scan_subdomain(self, subdomains):
        for subdomain in subdomains:
            try:
                full_url = f"https://{subdomain}.{self.url}"
                requests.get(full_url, headers=self.headers, timeout=2.5)
                with self.scan_lock:
                    print(f"\033[32m[*]{full_url}\033[0m")
                    self.result_file.write(f"https://{subdomain}.{self.url}\n")
                    self.result_file.flush()
                    os.fsync(self.result_file.fileno())
            except:
                with self.scan_lock:
                    print(f"\033[31m[!]{full_url}\033[0m")

class Icp:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Referer': 'strict-origin-when-cross-origin'
    }
    api = "https://m.ecjson.com/api?type=icp&domain="
    api2 = "&format=json"
    url = ""
    current_path = ""

    def Icp_menu(self):
        print("\n\033[32m[*]ICP查询菜单\033[0m")
        print("======================================================")
        print("可选择功能：1.输入要查询的域名 2.返回")

    def url_get(self):
        print("请输入要查询的域名：")
        try:
            self.url = input().strip()
            if not self.url:
                print("\033[31m[!]未输入域名！\033[0m")
                input("按回车继续ICP查询...")
                return False
            self.url = self.url.replace("https://", "").replace("http://", "").replace("www.", "")
            self.current_path = os.getcwd()
            if not re.match(r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}$", self.url):
                print("\033[31m[!]输入错误！\033[0m")
                input("按回车继续ICP查询...")
                return False
        except:
            print("\033[31m[!]输入错误！\033[0m")
            input("按回车继续ICP查询...")
            return False

    def icp_query(self):
        try:
            response = requests.get(self.api + self.url + self.api2, headers=self.headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    print(f"\033[32m[*]查询成功: \033[0m")
                    print(f"\033[32m[*]类型：{data.get('type', '未知类型')}\033[0m")
                    print(f"\033[32m[*]ICP编号：{data.get('icp', '未知ICP')}\033[0m")
                    print(f"\033[32m[*]单位：{data.get('unit', '未知单位')}\033[0m")
                    print(f"\033[32m[*]域名：{data.get('domain', '未知域名')}\033[0m")
                    print(f"\033[32m[*]审核时间：{data.get('time', '未知时间')}\033[0m")
                else:
                    print(f"\033[31m[!]查询失败: {data.get('msg', '未知错误')}\033[0m")
            else:
                print(f"\033[31m[!]API请求失败，状态码: {response.status_code}\033[0m")
        except Exception as e:
            print(f"\033[31m[!]查询出错: {str(e)}\033[0m")
        finally:
            input("按回车继续ICP查询...")

text = '\033[36m'+r"""


   ___        ____ __             ___ ___       ____          
  / _ ) __ __/_  // /_ ___  ____ / _/<  /__ __ / __/__ __ ___ 
 / _  |/ // / / // __// -_)/ __// _/ / // // // _/ / // // -_)
/____/ \_,_/ /_/ \__/ \__//_/  /_/  /_/ \_, //___/ \_, / \__/ 
                                       /___/      /___/       
                                                                                            
"""+"""\033[0m\033[32m
一款来自雪山盟的资产探测工具
[*]Version: 1.0.0
[*]Author: Bu7terf1y
[*]联系方式：Bu7terf1y
[*]Github:https://github.com/Bu7terf1y/Bu7terf1yEye\033[0m
"""

def main_menu():
    print("\n\033[32m[*]主菜单\033[0m")
    print("======================================================")
    print("可选择功能：1.子域名枚举 2.端口扫描 3.存活检测 4.icp查询 5.退出")

print(text)
while True:
    main_menu()
    main_choice = input("请输入选项：")
    if main_choice == "3":
        spider = Alive()
        while True:
            spider.menu()
            choice = input("请输入选项：")
            if choice == "1":
                print("\n\033[32m[*]存活检测-输入探测功能\033[0m")
                spider.clean()
                if spider.url_get() is False:
                    continue
                spider.distinct()
                spider.search()
            elif choice == "2":
                print("\n\033[32m[*]存活检测-批量探测功能\033[0m")
                spider.clean()
                if spider.file_get() is False:
                    continue
                spider.distinct()
                spider.search()
            elif choice == "3":
                print("\n\033[32m[*]存活检测-设置线程数\033[0m")
                spider.set_thread_count()
            elif choice == "4":
                print("\033[33m返回主菜单...\033[0m")
                break
            else:
                print("\033[31m[!]输入错误，请重新输入\033[0m")
                input("按回车继续存活检测...")
    elif main_choice == "2":
        port_scanner = Port()
        while True:
            port_scanner.port_menu()
            choice = input("请输入选项：")
            if choice == "1":
                print("\n\033[32m[*]端口扫描-输入目标\033[0m")
                port_scanner.target_get()
            elif choice == "2":
                print("\033[33m返回主菜单...\033[0m")
                break
            else:
                print("\033[31m[!]输入错误，请重新输入\033[0m")
                input("按回车继续端口扫描...")
    elif main_choice == "1":
        subdomain = Subdomain()
        while True:
            subdomain.Subdomain_menu()
            choice = input("请输入选项：")
            if choice == "1":
                if subdomain.url_get() is False:
                    continue
                subdomain.subdomain_scan()
            elif choice == "2":
                print("\033[33m返回主菜单...\033[0m")
                break
            else:
                print("\033[31m[!]输入错误，请重新输入\033[0m")
                input("按回车继续子域名枚举...")
    elif main_choice == "4":
        icp = Icp()
        while True:
            icp.Icp_menu()
            choice = input("请输入选项：")
            if choice == "1":
                if icp.url_get() is False:
                    continue
                icp.icp_query()
            elif choice == "2":
                print("\033[33m返回主菜单...\033[0m")
                break
            else:
                print("\033[31m[!]输入错误，请重新输入\033[0m")
                input("按回车继续ICP查询...")

    elif main_choice == "5":
        input("按回车退出...")
        break
    else:
        print("\033[31m[!]输入错误，请重新输入\033[0m")
        input("按回车继续...")