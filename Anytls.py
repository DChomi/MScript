#!/usr/bin/env python3
"""
Anytls.py - AnyTLS 协议部署模块
继承 MihomoBase 基类,实现 AnyTLS 协议的具体部署
"""

import sh
import sys
from BaseClass import MihomoBase


class AnyTLSInstaller(MihomoBase):
    """AnyTLS 协议安装器"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "AnyTLS"

    def get_deployment_config(self):
        """获取 AnyTLS 部署配置"""
        print("\n" + "=" * 42)
        print("⚙️ AnyTLS 部署配置")
        print("=" * 42 + "\n")

        # 获取域名
        while True:
            domain = input("请输入您的域名(例如: proxy.example.com): ").strip()
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
        print("\n🔑 密码配置:")
        password = input("请输入节点密码(留空则随机生成 UUID): ").strip()

        if not password:
            password = sh.uuidgen().strip()
            print(f"✅ 生成随机密码: {password}")
        else:
            print(f"✅ 使用自定义密码")

        # 确认配置
        print(f"\n📋 配置信息确认:")
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

        return domain, email, port, password, use_self_signed

    def generate_config(self, domain, port, password):
        """生成 AnyTLS 配置"""
        print("⚙️ 生成 AnyTLS 配置...")

        config_content = f"""listeners:
  - name: anytls-in-1
    type: anytls
    port: {port}
    listen: 0.0.0.0
    users:
      username1: '{password}'
    certificate: ./server.crt
    private-key: ./server.key
"""

        config_file = self.cert_dir / "config.yaml"
        config_file.write_text(config_content)

        print("✅ 配置文件生成完成")

    def print_final_info(self, domain, port, password, use_self_signed):
        """输出 AnyTLS 最终配置信息"""
        public_ip = self.get_public_ip()

        print("\n" + "=" * 46)
        print("✅ AnyTLS 部署完成!")
        print("=" * 46 + "\n")

        if use_self_signed:
            print("\n⚠️ 警告: 使用自签证书需要:")
            print("   - 客户端开启跳过证书验证 'skip-cert-verify: true'")
            print("   - 或允许使用不安全的证书(AllowInsecure)")
            input("\n按回车继续...")

        print("📋 AnyTLS 客户端配置:\n")

        skip_verify = "true" if use_self_signed else "false"

        print("---[ YAML 格式 ]---")
        print(f"- name: {domain}|AnyTLS")
        print(f"  server: {domain}")
        print(f"  type: anytls")
        print(f"  port: {port}")
        print(f"  password: {password}")
        print(f"  skip-cert-verify: {skip_verify}")
        print(f"  sni: {domain}")
        print(f"  udp: true")
        print(f"  tfo: true")
        print(f"  tls: true")
        print(f"  client-fingerprint: chrome\n")

        print("---[ Compact 格式 ]---")
        compact = f'- {{name: "{domain}|AnyTLS", type: anytls, server: {domain}, port: {port}, password: "{password}", skip-cert-verify: {skip_verify}, sni: {domain}, udp: true, tfo: true, tls: true, client-fingerprint: chrome}}'
        print(f"{compact}\n")

        insecure_flag = "1" if use_self_signed else "0"
        print("---[ URI 格式 ]---")
        uri = f"anytls://{password}@{domain}:{port}?peer={domain}&insecure={insecure_flag}&fastopen=1&udp=1#{domain}|AnyTLS"
        print(f"{uri}\n")

        print("=" * 46)
        print("📌 重要信息:")
        print(f"  服务器 IP: {public_ip}")
        print(f"  域名: {domain}")
        print(f"  端口: {port}")
        print(f"  密码: {password}\n")

        print("🔒 证书信息:")
        print(f"  证书位置: {self.cert_dir}/server.crt")
        print(f"  私钥位置: {self.cert_dir}/server.key")
        if use_self_signed:
            print(f"  类型: 自签证书 (有效期 365 天)")
        else:
            print(f"  自动续期: 已配置(acme.sh 会自动续期)\n")

        print("🎯 防火墙设置:")
        print(f"  请确保开放端口: {port}\n")
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

        if not use_self_signed:
            print("🔄 证书续期:")
            print(f"  查看证书: {self.acme_sh} --info -d {domain} --ecc")
            print(f"  手动续期: {self.acme_sh} --renew -d {domain} --ecc --force\n")

        print("=" * 46 + "\n")

        print("📊 当前服务状态:")
        try:
            sh.systemctl("status", "mihomo", "--no-pager", "-l", _fg=True)
        except:
            pass

        print("\n✅ 安装完成!请将上面的配置信息添加到您的客户端中或直接使用URI格式分享链接。")

    def install(self):
        """AnyTLS 完整安装流程"""
        try:
            print("\n" + "=" * 46)
            print("🚀 开始安装 AnyTLS")
            print("=" * 46)

            # 检查必要依赖
            self.check_dependencies()

            # 检测架构
            bin_arch, level = self.detect_architecture()

            # 安装 Mihomo
            self.install_mihomo(bin_arch, level)

            # 获取部署配置
            domain, email, port, password, use_self_signed = self.get_deployment_config()

            # 根据证书类型执行不同操作
            if use_self_signed:
                # 生成自签证书
                self.generate_self_signed_cert(domain)
            else:
                # 安装 acme.sh
                self.install_acme_sh(email)
                # 申请证书
                self.request_certificate(domain, email)

            # 生成配置
            self.generate_config(domain, port, password)

            # 创建服务
            self.create_systemd_service()

            # 输出最终信息
            self.print_final_info(domain, port, password, use_self_signed)

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

    installer = AnyTLSInstaller()
    installer.install()