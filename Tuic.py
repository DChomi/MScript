#!/usr/bin/env python3
"""
Tuic.py - TUIC V5 协议部署模块
继承 MihomoBase 基类,实现 TUIC V5 协议的具体部署
"""

import sh
import sys
from urllib.parse import quote
from BaseClass import MihomoBase


class TuicInstaller(MihomoBase):
    """TUIC V5 协议安装器"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "TUIC V5"

    def get_deployment_config(self):
        """获取 TUIC V5 部署配置"""
        print("\n" + "=" * 42)
        print("⚙️ TUIC V5 部署配置")
        print("=" * 42 + "\n")

        # 获取域名
        domain = self.get_domain_input()

        # 选择证书类型
        use_self_signed = self.get_cert_type_choice()

        # 获取邮箱(仅在使用正式证书时)
        email = None if use_self_signed else self.get_email_input()

        # 获取端口
        print("\n📌 端口配置:")
        port = self.get_port_input()

        # 获取用户名
        print("\n👤 用户配置:")
        username = self.get_password_or_uuid_input(use_uuid=False, prompt_type="用户名")

        # 获取密码
        print("\n🔑 密码配置:")
        password = self.get_password_or_uuid_input(use_uuid=False, prompt_type="密码")

        # 拥塞控制算法选择
        print("\n🚀 拥塞控制算法:")
        print("  1. bbr (推荐) - 适合大部分场景")
        print("  2. cubic - 传统算法")
        print("  3. new_reno - 保守算法")

        while True:
            cc_choice = input("\n请选择拥塞控制算法 (1/2/3, 默认 bbr): ").strip()
            if not cc_choice or cc_choice == '1':
                congestion_controller = 'bbr'
                break
            elif cc_choice == '2':
                congestion_controller = 'cubic'
                break
            elif cc_choice == '3':
                congestion_controller = 'new_reno'
                break
            else:
                print("❌ 无效选项,请重新输入")

        print(f"✅ 使用拥塞控制算法: {congestion_controller}")

        # 确认配置
        print(f"\n📋 配置信息确认:")
        print(f"  域名: {domain}")
        if not use_self_signed:
            print(f"  邮箱: {email}")
        print(f"  证书: {'自签证书' if use_self_signed else 'acme.sh 正式证书'}")
        print(f"  端口: {port}")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  拥塞控制: {congestion_controller}\n")

        confirm = input("确认无误?(y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ 已取消")
            sys.exit(1)

        return domain, email, port, username, password, congestion_controller, use_self_signed

    def generate_config(self, port, username, password, congestion_controller):
        """生成 TUIC V5 配置"""
        print("⚙️ 生成 TUIC V5 配置...")

        config_content = f"""listeners:
  - name: tuicv5-in
    type: tuic
    port: {port}
    listen: 0.0.0.0
    users:
      {username}: '{password}'
    certificate: ./server.crt
    private-key: ./server.key
    congestion-controller: {congestion_controller}
    max-idle-time: 15000
    authentication-timeout: 1000
    alpn:
      - h3
    max-udp-relay-packet-size: 1500
"""

        config_file = self.cert_dir / "config.yaml"
        config_file.write_text(config_content)

        print("✅ 配置文件生成完成")

    def print_final_info(self, domain, port, username, password, congestion_controller, use_self_signed):
        """输出 TUIC V5 最终配置信息"""
        public_ip = self.get_public_ip()

        print("\n" + "=" * 46)
        print("✅ TUIC V5 部署完成!")
        print("=" * 46 + "\n")

        if use_self_signed:
            print("\n⚠️ 警告: 使用自签证书需要:")
            print("   - 客户端开启跳过证书验证 'skip-cert-verify: true'")
            print("   - 或允许使用不安全的证书(AllowInsecure)")
            input("\n按回车继续...")

        print("📋 TUIC V5 客户端配置:\n")

        skip_verify = "true" if use_self_signed else "false"

        print("---[ YAML 格式 ]---")
        print(f"- name: {domain}|TUIC-V5")
        print(f"  server: {domain}")
        print(f"  type: tuic")
        print(f"  port: {port}")
        print(f"  uuid: {username}")
        print(f"  password: {password}")
        print(f"  skip-cert-verify: {skip_verify}")
        print(f"  sni: {domain}")
        print(f"  alpn:")
        print(f"    - h3")
        print(f"  congestion-controller: {congestion_controller}")
        print(f"  udp-relay-mode: native")
        print(f"  udp: true")
        print(f"  disable-sni: false\n")

        print("---[ Compact 格式 ]---")
        compact = f'- {{name: "{domain}|TUIC-V5", type: tuic, server: {domain}, port: {port}, uuid: {username}, password: "{password}", skip-cert-verify: {skip_verify}, sni: {domain}, alpn: [h3], congestion-controller: {congestion_controller}, udp-relay-mode: native, udp: true, disable-sni: false}}'
        print(f"{compact}\n")

        # URL编码用户名和密码
        encoded_username = quote(username, safe='')
        encoded_password = quote(password, safe='')
        insecure_flag = "1" if use_self_signed else "0"

        print("---[ URI 格式 ]---")
        uri = f"tuic://{encoded_username}%3A{encoded_password}@{domain}:{port}?sni={domain}&alpn=h3&congestion_control={congestion_controller}&allow_insecure={insecure_flag}#{quote(f'{domain}|TUIC-V5', safe='')}"
        print(f"{uri}\n")

        print("=" * 46)
        print("📌 重要信息:")
        print(f"  服务器 IP: {public_ip}")
        print(f"  域名: {domain}")
        print(f"  端口: {port}")
        print(f"  UUID: {username}")
        print(f"  密码: {password}")
        print(f"  拥塞控制: {congestion_controller}\n")

        print("🔒 证书信息:")
        print(f"  证书位置: {self.cert_dir}/server.crt")
        print(f"  私钥位置: {self.cert_dir}/server.key")
        if use_self_signed:
            print(f"  类型: 自签证书 (有效期 365 天)")
        else:
            print(f"  自动续期: 已配置(acme.sh 会自动续期)\n")

        print("🎯 防火墙设置:")
        print(f"  请确保开放端口: {port}/UDP (TUIC 主要使用 UDP)")
        print(f"  建议同时开放 TCP 以支持握手\n")
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

        print("💡 TUIC V5 协议特点:")
        print("  - 基于 QUIC 协议,性能优异")
        print("  - 原生 UDP 支持,适合游戏和语音")
        print("  - 支持 0-RTT 连接恢复")
        print("  - 多路复用,低延迟\n")

        print("📊 当前服务状态:")
        try:
            sh.systemctl("status", "mihomo", "--no-pager", "-l", _fg=True)
        except:
            pass

        print("\n✅ 安装完成!请将上面的配置信息添加到您的客户端中或直接使用URI格式分享链接。")

    def install(self):
        """TUIC V5 完整安装流程"""
        try:
            print("\n" + "=" * 46)
            print("🚀 开始安装 TUIC V5")
            print("=" * 46)

            # 检查必要依赖
            self.check_dependencies()

            # 检测架构
            bin_arch, level = self.detect_architecture()

            # 安装 Mihomo
            self.install_mihomo(bin_arch, level)

            # 获取部署配置
            domain, email, port, username, password, congestion_controller, use_self_signed = self.get_deployment_config()

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
            self.generate_config(port, username, password, congestion_controller)

            # 创建服务
            self.create_systemd_service()

            # 输出最终信息
            self.print_final_info(domain, port, username, password, congestion_controller, use_self_signed)

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

    installer = TuicInstaller()
    installer.install()