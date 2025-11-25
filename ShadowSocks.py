#!/usr/bin/env python3
"""
ShadowSocks.py - Shadowsocks 协议部署模块
继承 MihomoBase 基类,实现 Shadowsocks 2022 协议的具体部署
"""

import sh
import sys
import yaml
import subprocess
from BaseClass import MihomoBase


class ShadowSocksInstaller(MihomoBase):
    """Shadowsocks 协议安装器"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "Shadowsocks"

    def get_deployment_config(self):
        """获取 Shadowsocks 部署配置"""
        print("\n" + "=" * 42)
        print("⚙️  Shadowsocks 部署配置")
        print("=" * 42 + "\n")

        # 选择加密方法
        cipher = self.get_cipher_choice()

        # 获取端口
        print("\n📌 端口配置:")
        port = self.get_port_input()

        # 获取密码
        print("\n🔑 密码配置:")
        if cipher.startswith('2022'):
            password = self.get_2022_password(cipher)
        else:
            password = self.get_password_or_uuid_input(use_uuid=False, prompt_type="密码")

        # 选择传输层协议
        transport_type, transport_config = self.get_transport_config()

        # 确认配置
        config_info = {
            "加密方法": cipher,
            "端口": port,
            "密码": password if not cipher.startswith('2022') else f"{password[:16]}...",
            "传输协议": transport_type
        }

        # 添加传输层特定配置到确认信息
        if transport_type == "Shadow-TLS":
            config_info.update({
                "TLS版本": f"v{transport_config['version']}",
                "伪装域名": transport_config['handshake']['dest']
            })
        elif transport_type == "KCP":
            config_info.update({
                "KCP模式": transport_config['mode'],
                "加密方式": transport_config['crypt']
            })

        if not self.confirm_config(config_info):
            sys.exit(1)

        return cipher, port, password, transport_type, transport_config

    def get_cipher_choice(self):
        """选择加密方法"""
        print("🔐 加密方法:")
        print("  1. 2022-blake3-aes-128-gcm (推荐,需要 16 字节密码)")
        print("  2. 2022-blake3-aes-256-gcm (推荐,需要 32 字节密码)")
        print("  3. 2022-blake3-chacha20-poly1305 (推荐,需要 32 字节密码)")
        print("  4. aes-128-gcm (传统方法)")
        print("  5. aes-256-gcm (传统方法)")
        print("  6. chacha20-ietf-poly1305 (传统方法)")
        print("  7. xchacha20-ietf-poly1305 (传统方法)")

        cipher_map = {
            '1': '2022-blake3-aes-128-gcm',
            '2': '2022-blake3-aes-256-gcm',
            '3': '2022-blake3-chacha20-poly1305',
            '4': 'aes-128-gcm',
            '5': 'aes-256-gcm',
            '6': 'chacha20-ietf-poly1305',
            '7': 'xchacha20-ietf-poly1305'
        }

        while True:
            choice = input("\n请选择加密方法 (1-7): ").strip()
            if choice in cipher_map:
                cipher = cipher_map[choice]
                print(f"✅ 已选择: {cipher}")
                return cipher
            print("❌ 无效选项,请重新输入")

    def get_2022_password(self, cipher):
        """获取 Shadowsocks 2022 密码"""
        # 确定密码长度
        if 'aes-128' in cipher:
            length = 16
        else:
            length = 32

        print(f"\n💡 {cipher} 需要 {length} 字节的 base64 编码密码")
        password_input = input("请输入密码(留空则自动生成): ").strip()

        if not password_input:
            # 生成随机密码
            try:
                result = subprocess.run(
                    f"openssl rand -base64 {length}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                password = result.stdout.strip()
                print(f"✅ 生成随机密码: {password}")
                return password
            except Exception as e:
                print(f"❌ 生成密码失败: {e}")
                sys.exit(1)
        else:
            print(f"✅ 使用自定义密码")
            return password_input

    def get_transport_config(self):
        """获取传输层协议配置"""
        print("\n🚀 传输层协议:")
        print("  1. 直接传输 (无额外封装)")
        print("  2. Shadow-TLS (TLS 伪装,推荐)")
        print("  3. KCP (UDP 加速)")

        while True:
            choice = input("\n请选择传输协议 (1-3): ").strip()

            if choice == '1':
                return "直接传输", None
            elif choice == '2':
                return "Shadow-TLS", self.config_shadow_tls()
            elif choice == '3':
                return "KCP", self.config_kcp()
            else:
                print("❌ 无效选项,请重新输入")

    def config_shadow_tls(self):
        """配置 Shadow-TLS"""
        print("\n🔐 Shadow-TLS 配置:")
        print("  Shadow-TLS 可以将流量伪装成正常的 TLS 流量")

        # 选择版本
        print("\n📌 选择版本:")
        print("  1. v1 (基础版本)")
        print("  2. v2 (支持密码认证)")
        print("  3. v3 (支持多用户,推荐)")

        while True:
            version_choice = input("\n请选择版本 (1-3): ").strip()
            if version_choice in ['1', '2', '3']:
                version = int(version_choice)
                break
            print("❌ 无效选项,请重新输入")

        # 获取伪装域名
        print("\n🌐 伪装目标配置:")
        print("  输入一个真实存在的 HTTPS 网站(如: www.bing.com:443)")
        handshake_dest = input("伪装域名:端口 [默认: www.bing.com:443]: ").strip()
        if not handshake_dest:
            handshake_dest = "www.bing.com:443"

        config = {
            'enable': True,
            'version': version,
            'handshake': {
                'dest': handshake_dest
            }
        }

        # v2 需要密码
        if version == 2:
            password = input("\n请输入 Shadow-TLS 密码 [默认: password]: ").strip()
            if not password:
                password = "password"
            config['password'] = password

        # v3 支持多用户
        elif version == 3:
            print("\n👥 配置用户:")
            users = []
            user_count = input("需要配置几个用户? [默认: 1]: ").strip()
            user_count = int(user_count) if user_count.isdigit() else 1

            for i in range(user_count):
                username = input(f"\n用户 {i + 1} 名称 [默认: user{i + 1}]: ").strip()
                if not username:
                    username = f"user{i + 1}"

                user_password = input(f"用户 {i + 1} 密码 [默认: password]: ").strip()
                if not user_password:
                    user_password = "password"

                users.append({
                    'name': username,
                    'password': user_password
                })

            config['users'] = users

        print(f"\n✅ Shadow-TLS v{version} 配置完成")
        return config

    def config_kcp(self):
        """配置 KCP"""
        print("\n🚀 KCP 配置:")
        print("  KCP 是基于 UDP 的传输协议,适合不稳定网络")

        # 预设模式
        print("\n📌 选择传输模式:")
        print("  1. fast3 (最快,适合高速网络)")
        print("  2. fast2 (较快)")
        print("  3. fast  (快速,推荐)")
        print("  4. normal (正常)")

        mode_map = {'1': 'fast3', '2': 'fast2', '3': 'fast', '4': 'normal'}
        while True:
            mode_choice = input("\n请选择模式 (1-4) [默认: 3]: ").strip()
            if not mode_choice:
                mode_choice = '3'
            if mode_choice in mode_map:
                mode = mode_map[mode_choice]
                break
            print("❌ 无效选项,请重新输入")

        # 加密方式
        print("\n🔐 选择加密方式:")
        print("  1. aes     (推荐)")
        print("  2. aes-128")
        print("  3. aes-192")
        print("  4. salsa20")
        print("  5. none    (无加密,最快)")

        crypt_map = {'1': 'aes', '2': 'aes-128', '3': 'aes-192', '4': 'salsa20', '5': 'none'}
        while True:
            crypt_choice = input("\n请选择加密方式 (1-5) [默认: 1]: ").strip()
            if not crypt_choice:
                crypt_choice = '1'
            if crypt_choice in crypt_map:
                crypt = crypt_map[crypt_choice]
                break
            print("❌ 无效选项,请重新输入")

        # 预共享密钥
        key = input("\n请输入预共享密钥 [默认: it's a secrect]: ").strip()
        if not key:
            key = "it's a secrect"

        config = {
            'enable': True,
            'key': key,
            'crypt': crypt,
            'mode': mode,
            'conn': 1,
            'autoexpire': 0,
            'scavengettl': 600,
            'mtu': 1350,
            'sndwnd': 128,
            'rcvwnd': 512,
            'datashard': 10,
            'parityshard': 3,
            'dscp': 0,
            'nocomp': False,
            'acknodelay': False,
            'nodelay': 0,
            'interval': 50,
            'resend': 0,
            'sockbuf': 4194304,
            'smuxver': 1,
            'smuxbuf': 4194304,
            'streambuf': 2097152,
            'keepalive': 10
        }

        print(f"\n✅ KCP {mode} 模式配置完成")
        return config

    def generate_config(self, cipher, port, password, transport_type, transport_config):
        """生成 Shadowsocks 配置"""
        print("⚙️  生成 Shadowsocks 配置...")

        # 确保目录存在
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        listener_config = {
            'name': 'ss-in',
            'type': 'shadowsocks',
            'port': port,
            'listen': '0.0.0.0',
            'cipher': cipher,
            'password': password,
            'udp': True
        }

        # 添加传输层配置
        if transport_type == "Shadow-TLS" and transport_config:
            listener_config['shadow-tls'] = transport_config
        elif transport_type == "KCP" and transport_config:
            listener_config['kcp-tun'] = transport_config

        config = {
            'listeners': [listener_config]
        }

        config_file = self.cert_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        print("✅ 配置文件生成完成")

        # 显示生成的配置内容
        print("\n📄 生成的配置文件内容:")
        print("─" * 50)
        with open(config_file, 'r', encoding='utf-8') as f:
            print(f.read())
        print("─" * 50)

    def print_final_info(self, cipher, port, password, transport_type, transport_config):
        """输出 Shadowsocks 最终配置信息"""
        public_ip = self.get_public_ip()

        print("\n" + "=" * 46)
        print("✅ Shadowsocks 部署完成!")
        print("=" * 46 + "\n")

        print("📋 Shadowsocks 客户端配置:\n")

        # 基础配置
        print("---[ YAML 格式 ]---")
        print(f"- name: {public_ip}|SS")
        print(f"  server: {public_ip}")
        print(f"  type: ss")
        print(f"  port: {port}")
        print(f"  cipher: {cipher}")
        print(f"  password: {password}")
        print(f"  udp: true")

        # 添加传输层配置
        if transport_type == "Shadow-TLS":
            print(f"  plugin: shadow-tls")
            plugin_opts = {
                'version': transport_config['version'],
                'host': transport_config['handshake']['dest'].split(':')[0]
            }
            if transport_config.get('password'):
                plugin_opts['password'] = transport_config['password']
            print(f"  plugin-opts:")
            for key, value in plugin_opts.items():
                print(f"    {key}: {value}")
        elif transport_type == "KCP":
            print(f"  plugin: kcptun")
            print(f"  plugin-opts:")
            print(f"    mode: {transport_config['mode']}")
            print(f"    key: {transport_config['key']}")
            print(f"    crypt: {transport_config['crypt']}")
        else:
            print(f"  plugin: ''")
            print(f"  plugin-opts: {{}}")
        print()

        # Compact 格式
        print("---[ Compact 格式 ]---")
        if transport_type == "直接传输":
            compact = f'- {{name: "{public_ip}|SS", type: ss, server: {public_ip}, port: {port}, cipher: {cipher}, password: "{password}", udp: true}}'
        else:
            compact = f'- {{name: "{public_ip}|SS-{transport_type}", type: ss, server: {public_ip}, port: {port}, cipher: {cipher}, password: "{password}", udp: true}}'
        print(f"{compact}\n")

        # URI 格式
        import base64
        userinfo = f"{cipher}:{password}"
        userinfo_b64 = base64.urlsafe_b64encode(userinfo.encode()).decode().rstrip('=')
        print("---[ URI 格式 ]---")

        if transport_type == "Shadow-TLS":
            tag = f"{public_ip}|SS-ShadowTLS"
        elif transport_type == "KCP":
            tag = f"{public_ip}|SS-KCP"
        else:
            tag = f"{public_ip}|SS"

        uri = f"ss://{userinfo_b64}@{public_ip}:{port}#{tag}"
        print(f"{uri}\n")

        print("=" * 46)
        print("📌 重要信息:")
        print(f"  服务器 IP: {public_ip}")
        print(f"  端口: {port}")
        print(f"  加密方法: {cipher}")
        print(f"  密码: {password}")
        print(f"  传输协议: {transport_type}")

        if transport_type == "Shadow-TLS":
            print(f"\n🔐 Shadow-TLS 配置:")
            print(f"  版本: v{transport_config['version']}")
            print(f"  伪装域名: {transport_config['handshake']['dest']}")
            if transport_config.get('password'):
                print(f"  TLS密码: {transport_config['password']}")
            if transport_config.get('users'):
                print(f"  用户列表:")
                for user in transport_config['users']:
                    print(f"    - {user['name']}: {user['password']}")
        elif transport_type == "KCP":
            print(f"\n🚀 KCP 配置:")
            print(f"  模式: {transport_config['mode']}")
            print(f"  加密: {transport_config['crypt']}")
            print(f"  密钥: {transport_config['key']}")
        print()

        print("🎯 防火墙设置:")
        print(f"  请确保开放端口: {port}")
        if transport_type == "KCP":
            print(f"  注意: KCP 使用 UDP 协议")
        print()
        print("  Ubuntu/Debian:")
        print(f"    sudo ufw allow {port}/tcp")
        print(f"    sudo ufw allow {port}/udp\n")
        print("  CentOS/RHEL:")
        print(f"    sudo firewall-cmd --permanent --add-port={port}/tcp")
        print(f"    sudo firewall-cmd --permanent --add-port={port}/udp")
        print(f"    sudo firewall-cmd --reload\n")

        print("=" * 46 + "\n")

        print("🔧 服务管理命令:")
        print("  查看状态: systemctl status mihomo")
        print("  重启服务: systemctl restart mihomo")
        print("  查看日志: journalctl -u mihomo -f")
        print("  停止服务: systemctl stop mihomo\n")

        if transport_type != "直接传输":
            print("💡 客户端配置说明:")
            if transport_type == "Shadow-TLS":
                print("  - 确保客户端支持 shadow-tls 插件")
                print("  - 部分客户端可能需要额外安装插件")
            elif transport_type == "KCP":
                print("  - 确保客户端支持 kcptun 插件")
                print("  - KCP 可显著提升不稳定网络下的速度")
            print()

        print("=" * 46 + "\n")

        print("📊 当前服务状态（Docker方式部署无法查看状态）:")
        try:
            sh.systemctl("status", "mihomo", "--no-pager", "-l", _fg=True)
        except:
            pass

        print("\n✅ 安装完成!请将上面的配置信息添加到您的客户端中或直接使用URI格式分享链接。")

    def install(self):
        """Shadowsocks 完整安装流程"""
        try:
            print("\n" + "=" * 46)
            print("🚀 开始安装 Shadowsocks")
            print("=" * 46)

            # 检查必要依赖
            self.check_dependencies()

            # 选择部署方式
            deployment_method = self.get_deployment_method()

            # 检测架构
            bin_arch, level = self.detect_architecture()

            # 只有直接部署才需要安装 Mihomo
            if deployment_method == 'systemd':
                self.install_mihomo(bin_arch, level)

            # 获取部署配置
            cipher, port, password, transport_type, transport_config = self.get_deployment_config()

            # 生成配置
            self.generate_config(cipher, port, password, transport_type, transport_config)

            # 根据部署方式执行不同操作
            if deployment_method == 'systemd':
                # 创建 systemd 服务
                self.create_systemd_service()
            else:
                # 创建并启动 Docker 容器
                self.create_docker_compose_file(self.cert_dir, self.protocol_name, port)
                self.start_docker_service(self.cert_dir)

            # 输出最终信息
            self.print_final_info(cipher, port, password, transport_type, transport_config)

        except KeyboardInterrupt:
            print("\n\n❌ 用户取消操作")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 安装过程出错: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    # 检查是否为 root 用户
    if sh.whoami().strip() != "root":
        print("❌ 请使用 root 用户运行此脚本")
        sys.exit(1)

    installer = ShadowSocksInstaller()
    installer.install()