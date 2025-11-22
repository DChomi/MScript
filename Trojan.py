#!/usr/bin/env python3
"""
Trojan.py - Trojan 协议部署模块
继承 MihomoBase 基类,实现 Trojan 协议的具体部署
支持 TLS 和 Reality 两种模式
"""

import sh
import sys
import subprocess
from BaseClass import MihomoBase


class TrojanInstaller(MihomoBase):
    """Trojan 协议安装器"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "Trojan"

    def generate_reality_keypair(self):
        """生成 Reality 密钥对"""
        print("\n🔑 生成 Reality 密钥对...")
        try:
            result = subprocess.run(
                ["mihomo", "generate", "reality-keypair"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception("密钥对生成失败")

            output = result.stdout.strip()
            lines = output.split('\n')

            private_key = None
            public_key = None

            for line in lines:
                if line.startswith("PrivateKey:"):
                    private_key = line.split(":", 1)[1].strip()
                elif line.startswith("PublicKey:"):
                    public_key = line.split(":", 1)[1].strip()

            if not private_key or not public_key:
                raise Exception("无法解析密钥对")

            print(f"✅ PrivateKey: {private_key}")
            print(f"✅ PublicKey: {public_key}")

            return private_key, public_key

        except Exception as e:
            print(f"❌ 密钥对生成失败: {e}")
            sys.exit(1)

    def generate_short_id(self):
        """生成 16 位 ShortID (只包含 0-9 和 a-f)"""
        import random
        chars = '0123456789abcdef'
        short_id = ''.join(random.choice(chars) for _ in range(16))
        return short_id

    def get_deployment_config(self):
        """获取 Trojan 部署配置"""
        print("\n" + "=" * 42)
        print("⚙️ Trojan 部署配置")
        print("=" * 42 + "\n")

        # 选择模式
        print("📡 传输模式:")
        print("  1. TLS 模式 (需要域名和证书)")
        print("  2. Reality 模式 (无需证书,更隐蔽)")

        while True:
            mode_choice = input("\n请选择模式 (1/2): ").strip()
            if mode_choice in ['1', '2']:
                break
            print("❌ 无效选项,请重新输入")

        use_reality = (mode_choice == '2')

        # 共同配置项
        domain = None
        email = None
        use_self_signed = False
        fake_domain = None
        private_key = None
        public_key = None
        short_id = None

        if use_reality:
            print("\n🎭 Reality 模式配置")
            print("=" * 42)

            # Reality 模式下获取伪装域名
            fake_domain = input("\n请输入伪装域名(留空则使用 www.microsoft.com): ").strip()
            if not fake_domain:
                fake_domain = "www.microsoft.com"
                print(f"✅ 使用默认伪装域名: {fake_domain}")

            # 生成 Reality 密钥对
            private_key, public_key = self.generate_reality_keypair()

            # 生成 ShortID
            short_id = self.generate_short_id()
            print(f"✅ ShortID: {short_id}")

        else:
            print("\n🔒 TLS 模式配置")
            print("=" * 42)

            # 获取域名
            while True:
                domain = input("\n请输入您的域名(例如: proxy.example.com): ").strip()
                if not domain:
                    print("❌ 域名不能为空")
                    continue

                if not self.validate_domain(domain):
                    print("❌ 域名格式不正确")
                    continue
                break

            # 选择证书类型
            print("\n📜 证书类型:")
            print("  1. 使用 acme.sh 申请正式证书 (推荐)")
            print("  2. 使用自签证书 (需要客户端跳过证书验证)")

            while True:
                cert_choice = input("\n请选择证书类型 (1/2): ").strip()
                if cert_choice in ['1', '2']:
                    break
                print("❌ 无效选项,请重新输入")

            use_self_signed = (cert_choice == '2')

            if use_self_signed:
                print("\n⚠️ 警告: 使用自签证书需要:")
                print("   - 客户端开启跳过证书验证 'skip-cert-verify: true'")
                print("   - 或允许使用不安全的证书(AllowInsecure)")
                email = None
            else:
                # 获取邮箱
                while True:
                    email = input("\n请输入您的邮箱(用于接收证书通知): ").strip()
                    if not email:
                        print("❌ 邮箱不能为空")
                        continue

                    if not self.validate_email(email):
                        print("❌ 邮箱格式不正确")
                        continue
                    break

        # 获取端口
        print("\n📌 端口配置:")
        port_input = input("请输入端口号(留空则随机生成 20000-60000): ").strip()

        if port_input:
            try:
                port = int(port_input)
                if port < 1 or port > 65535:
                    print("❌ 端口号必须在 1-65535 之间,使用随机端口")
                    port = self.random_free_port()
                elif port < 1024:
                    print("⚠️ 警告: 使用小于 1024 的端口需要 root 权限")
            except ValueError:
                print("❌ 无效的端口号,使用随机端口")
                port = self.random_free_port()
        else:
            port = self.random_free_port()

        print(f"✅ 使用端口: {port}")

        # 获取密码
        print("\n🔐 密码配置:")
        password = input("请输入密码(留空则随机生成 UUID): ").strip()

        if not password:
            password = sh.uuidgen().strip()
            print(f"✅ 生成随机密码: {password}")
        else:
            print(f"✅ 使用自定义密码")

        # 确认配置
        print(f"\n📋 配置信息确认:")
        print(f"  模式: {'Reality' if use_reality else 'TLS'}")

        if use_reality:
            print(f"  伪装域名: {fake_domain}")
            print(f"  PrivateKey: {private_key}")
            print(f"  PublicKey: {public_key}")
            print(f"  ShortID: {short_id}")
        else:
            print(f"  域名: {domain}")
            if not use_self_signed:
                print(f"  邮箱: {email}")
            print(f"  证书: {'自签证书' if use_self_signed else 'acme.sh 正式证书'}")

        print(f"  端口: {port}")
        print(f"  密码: {password}\n")

        confirm = input("确认无误?(y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ 已取消")
            sys.exit(1)

        return {
            'use_reality': use_reality,
            'domain': domain,
            'email': email,
            'port': port,
            'password': password,
            'use_self_signed': use_self_signed,
            'fake_domain': fake_domain,
            'private_key': private_key,
            'public_key': public_key,
            'short_id': short_id
        }

    def generate_config(self, config):
        """生成 Trojan 配置"""
        print("⚙️ 生成 Trojan 配置...")

        self.cert_dir.mkdir(parents=True, exist_ok=True)

        if config['use_reality']:
            # Reality 模式配置
            config_content = f"""listeners:
  - name: trojan-in-1
    type: trojan
    port: {config['port']}
    listen: 0.0.0.0
    users:
      - username: user1
        password: {config['password']}
    reality-config:
      dest: {config['fake_domain']}:443
      private-key: {config['private_key']}
      short-id:
        - "{config['short_id']}"
      server-names:
        - {config['fake_domain']}
"""
        else:
            # TLS 模式配置
            config_content = f"""listeners:
  - name: trojan-in-1
    type: trojan
    port: {config['port']}
    listen: 0.0.0.0
    users:
      - username: user1
        password: {config['password']}
    certificate: ./server.crt
    private-key: ./server.key
"""

        config_file = self.cert_dir / "config.yaml"
        config_file.write_text(config_content)

        print("✅ 配置文件生成完成")

    def print_final_info(self, config):
        """输出 Trojan 最终配置信息"""
        public_ip = self.get_public_ip()

        print("\n" + "=" * 46)
        print("✅ Trojan 部署完成!")
        print("=" * 46 + "\n")

        mode_name = "Reality" if config['use_reality'] else "TLS"

        if not config['use_reality'] and config['use_self_signed']:
            print("\n⚠️ 警告: 使用自签证书需要:")
            print("   - 客户端开启跳过证书验证 'skip-cert-verify: true'")
            print("   - 或允许使用不安全的证书(AllowInsecure)")
            input("\n按回车继续...")

        print(f"📋 Trojan ({mode_name} 模式) 客户端配置:\n")

        # YAML 格式
        print("---[ YAML 格式 ]---")
        if config['use_reality']:
            server_display = public_ip
            sni_display = config['fake_domain']
            print(f"- name: Trojan|Reality|{config['fake_domain']}")
            print(f"  server: {server_display}")
            print(f"  type: trojan")
            print(f"  port: {config['port']}")
            print(f"  password: {config['password']}")
            print(f"  udp: true")
            print(f"  sni: {sni_display}")
            print(f"  reality-opts:")
            print(f"    public-key: {config['public_key']}")
            print(f"    short-id: {config['short_id']}")
            print(f"  client-fingerprint: chrome\n")
        else:
            server_display = config['domain']
            skip_verify = "true" if config['use_self_signed'] else "false"
            print(f"- name: Trojan|TLS|{config['domain']}")
            print(f"  server: {server_display}")
            print(f"  type: trojan")
            print(f"  port: {config['port']}")
            print(f"  password: {config['password']}")
            print(f"  udp: true")
            print(f"  sni: {config['domain']}")
            print(f"  skip-cert-verify: {skip_verify}")
            print(f"  client-fingerprint: chrome\n")

        # Compact 格式
        print("---[ Compact 格式 ]---")
        if config['use_reality']:
            compact = f'- {{name: "Trojan|Reality|{config["fake_domain"]}", type: trojan, server: {public_ip}, port: {config["port"]}, password: {config["password"]}, udp: true, sni: {config["fake_domain"]}, reality-opts: {{public-key: {config["public_key"]}, short-id: {config["short_id"]}}}, client-fingerprint: chrome}}'
        else:
            skip_verify = "true" if config['use_self_signed'] else "false"
            compact = f'- {{name: "Trojan|TLS|{config["domain"]}", type: trojan, server: {config["domain"]}, port: {config["port"]}, password: {config["password"]}, udp: true, sni: {config["domain"]}, skip-cert-verify: {skip_verify}, client-fingerprint: chrome}}'
        print(f"{compact}\n")

        # URI 格式
        print("---[ URI 格式 ]---")
        if config['use_reality']:
            uri = f"trojan://{config['password']}@{public_ip}:{config['port']}?security=reality&sni={config['fake_domain']}&fp=chrome&pbk={config['public_key']}&sid={config['short_id']}&type=tcp&headerType=none#Trojan|Reality|{config['fake_domain']}"
        else:
            uri = f"trojan://{config['password']}@{config['domain']}:{config['port']}?security=tls&sni={config['domain']}&fp=chrome&type=tcp&headerType=none#Trojan|TLS|{config['domain']}"
        print(f"{uri}\n")

        print("=" * 46)
        print("📌 重要信息:")
        print(f"  服务器 IP: {public_ip}")
        print(f"  模式: {mode_name}")

        if config['use_reality']:
            print(f"  伪装域名: {config['fake_domain']}")
            print(f"  PublicKey: {config['public_key']}")
        else:
            print(f"  域名: {config['domain']}")

        print(f"  端口: {config['port']}")
        print(f"  密码: {config['password']}\n")

        if config['use_reality']:
            print("🎭 Reality 配置:")
            print(f"  PrivateKey (服务端): {config['private_key']}")
            print(f"  PublicKey (客户端): {config['public_key']}")
            print(f"  ShortID: {config['short_id']}")
            print(f"  伪装域名: {config['fake_domain']}\n")
        else:
            print("🔒 证书信息:")
            print(f"  证书位置: {self.cert_dir}/server.crt")
            print(f"  私钥位置: {self.cert_dir}/server.key")
            if config['use_self_signed']:
                print(f"  类型: 自签证书 (有效期 365 天)")
            else:
                print(f"  自动续期: 已配置(acme.sh 会自动续期)\n")

        print("🎯 防火墙设置:")
        print(f"  请确保开放端口: {config['port']}\n")
        print("  Ubuntu/Debian:")
        print(f"    sudo ufw allow {config['port']}/tcp")
        print(f"    sudo ufw allow {config['port']}/udp\n")
        print("  CentOS/RHEL:")
        print(f"    sudo firewall-cmd --permanent --add-port={config['port']}/tcp")
        print(f"    sudo firewall-cmd --permanent --add-port={config['port']}/udp")
        print(f"    sudo firewall-cmd --reload\n")

        print("=" * 46 + "\n")

        print("🔧 服务管理命令:")
        print("  查看状态: systemctl status mihomo")
        print("  重启服务: systemctl restart mihomo")
        print("  查看日志: journalctl -u mihomo -f")
        print("  停止服务: systemctl stop mihomo\n")

        if not config['use_reality'] and not config['use_self_signed']:
            print("🔄 证书续期:")
            print(f"  查看证书: {self.acme_sh} --info -d {config['domain']} --ecc")
            print(f"  手动续期: {self.acme_sh} --renew -d {config['domain']} --ecc --force\n")

        print("=" * 46 + "\n")

        print("📊 当前服务状态:")
        try:
            sh.systemctl("status", "mihomo", "--no-pager", "-l", _fg=True)
        except:
            pass

        print("\n✅ 安装完成!请将上面的配置信息添加到您的客户端中或直接使用URI格式分享链接。")

    def install(self):
        """Trojan 完整安装流程"""
        try:
            print("\n" + "=" * 46)
            print("🚀 开始安装 Trojan")
            print("=" * 46)

            # 检查必要依赖
            self.check_dependencies()

            # 检测架构
            bin_arch, level = self.detect_architecture()

            # 安装 Mihomo
            self.install_mihomo(bin_arch, level)

            # 获取部署配置
            config = self.get_deployment_config()

            # 根据模式执行不同操作
            if config['use_reality']:
                # Reality 模式不需要证书
                print("\n✅ Reality 模式无需证书配置")
            else:
                # TLS 模式需要证书
                if config['use_self_signed']:
                    # 生成自签证书
                    self.generate_self_signed_cert(config['domain'])
                else:
                    # 安装 acme.sh
                    self.install_acme_sh(config['email'])
                    # 申请证书
                    self.request_certificate(config['domain'], config['email'])

            # 生成配置
            self.generate_config(config)

            # 创建服务
            self.create_systemd_service()

            # 输出最终信息
            self.print_final_info(config)

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

    installer = TrojanInstaller()
    installer.install()