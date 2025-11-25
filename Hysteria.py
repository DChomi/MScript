#!/usr/bin/env python3
"""
Hysteria.py - Hysteria2 协议部署模块
继承 MihomoBase 基类,实现 Hysteria2 协议的具体部署
"""

import sh
import sys
import yaml
from urllib.parse import quote
from BaseClass import MihomoBase


class HysteriaInstaller(MihomoBase):
    """Hysteria2 协议安装器"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "Hysteria2"

    def get_deployment_config(self):
        """获取 Hysteria2 部署配置"""
        print("\n" + "=" * 42)
        print("⚙️ Hysteria2 部署配置")
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
        print(f"✅ 使用端口: {port}")

        # 获取用户名
        print("\n👤 用户配置:")
        username = self.get_password_or_uuid_input(use_uuid=False, prompt_type="用户名")

        # 获取密码
        print("\n🔑 密码配置:")
        password = self.get_password_or_uuid_input(use_uuid=False, prompt_type="密码")

        # 带宽配置
        print("\n🚀 带宽配置 (单位: Mbps):")
        print("  提示: 请根据您的 VPS 实际带宽设置")
        print("  常见配置: 100/200/500/1000")

        # 上行带宽
        up_input = input("\n请输入上行带宽 (留空默认 1000 Mbps): ").strip()
        if up_input:
            try:
                up_mbps = int(up_input)
                if up_mbps <= 0:
                    print("❌ 带宽必须大于 0,使用默认值 1000")
                    up_mbps = 1000
            except ValueError:
                print("❌ 无效的带宽值,使用默认值 1000")
                up_mbps = 1000
        else:
            up_mbps = 1000

        print(f"✅ 上行带宽: {up_mbps} Mbps")

        # 下行带宽
        down_input = input("请输入下行带宽 (留空默认 1000 Mbps): ").strip()
        if down_input:
            try:
                down_mbps = int(down_input)
                if down_mbps <= 0:
                    print("❌ 带宽必须大于 0,使用默认值 1000")
                    down_mbps = 1000
            except ValueError:
                print("❌ 无效的带宽值,使用默认值 1000")
                down_mbps = 1000
        else:
            down_mbps = 1000

        print(f"✅ 下行带宽: {down_mbps} Mbps")

        # QUIC 混淆配置
        print("\n🔒 QUIC 流量混淆:")
        print("  提示: 启用混淆可以增强抗封锁能力")
        print("  ⚠️  注意: 启用后将失去 HTTP/3 伪装能力")

        enable_obfs = input("\n是否启用 QUIC 混淆? (y/n, 默认 n): ").strip().lower()

        if enable_obfs in ['y', 'yes']:
            obfs_type = "salamander"

            # QUIC 混淆密码
            obfs_password = input("\n请输入 QUIC 混淆密码 (留空则自动生成): ").strip()

            if not obfs_password:
                obfs_password = sh.uuidgen().strip()
                print(f"✅ 生成随机混淆密码: {obfs_password}")
            else:
                print(f"✅ 使用自定义混淆密码")
        else:
            obfs_type = None
            obfs_password = None
            print("✅ 未启用 QUIC 混淆")

        # 确认配置
        print(f"\n📋 配置信息确认:")
        print(f"  域名: {domain}")
        if not use_self_signed:
            print(f"  邮箱: {email}")
        print(f"  证书: {'自签证书' if use_self_signed else 'acme.sh 正式证书'}")
        print(f"  端口: {port}")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  上行带宽: {up_mbps} Mbps")
        print(f"  下行带宽: {down_mbps} Mbps")
        if obfs_type:
            print(f"  QUIC 混淆: 已启用 ({obfs_type})")
            print(f"  混淆密码: {obfs_password}")
        else:
            print(f"  QUIC 混淆: 未启用")
        print()

        confirm = input("确认无误?(y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ 已取消")
            sys.exit(1)

        return domain, email, port, username, password, up_mbps, down_mbps, obfs_type, obfs_password, use_self_signed

    def generate_config(self, port, username, password, up_mbps, down_mbps, obfs_type, obfs_password):
        """生成 Hysteria2 配置"""
        print("⚙️ 生成 Hysteria2 配置...")

        listener = {
            'name': 'hy2-in',
            'type': 'hysteria2',
            'port': port,
            'listen': '0.0.0.0',
            'users': {
                username: password
            },
            'up': up_mbps,
            'down': down_mbps,
            'ignore-client-bandwidth': False,
            'masquerade': '',
            'alpn': ['h3'],
            'certificate': './server.crt',
            'private-key': './server.key'
        }

        # 添加混淆配置
        if obfs_type and obfs_password:
            listener['obfs'] = obfs_type
            listener['obfs-password'] = obfs_password

        config = {'listeners': [listener]}

        config_file = self.cert_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        print("✅ 配置文件生成完成")

    def print_final_info(self, domain, port, username, password, up_mbps, down_mbps, obfs_type, obfs_password,
                         use_self_signed):
        """输出 Hysteria2 最终配置信息"""
        public_ip = self.get_public_ip()

        print("\n" + "=" * 46)
        print("✅ Hysteria2 部署完成!")
        print("=" * 46 + "\n")

        if use_self_signed:
            print("\n⚠️ 警告: 使用自签证书需要:")
            print("   - 客户端开启跳过证书验证 'skip-cert-verify: true'")
            print("   - 或允许使用不安全的证书(AllowInsecure)")
            input("\n按回车继续...")

        print("📋 Hysteria2 客户端配置:\n")

        skip_verify = "true" if use_self_signed else "false"

        print("---[ YAML 格式 ]---")
        print(f"- name: {domain}|Hysteria2")
        print(f"  server: {domain}")
        print(f"  type: hysteria2")
        print(f"  port: {port}")
        print(f"  password: {password}")
        print(f"  skip-cert-verify: {skip_verify}")
        print(f"  sni: {domain}")
        print(f"  alpn:")
        print(f"    - h3")

        if obfs_type and obfs_password:
            print(f"  obfs: {obfs_type}")
            print(f"  obfs-password: {obfs_password}")

        print(f"  up: {up_mbps}")
        print(f"  down: {down_mbps}")
        print(f"  udp: true\n")

        print("---[ Compact 格式 ]---")
        compact_parts = [
            f'name: "{domain}|Hysteria2"',
            f'type: hysteria2',
            f'server: {domain}',
            f'port: {port}',
            f'password: "{password}"',
            f'skip-cert-verify: {skip_verify}',
            f'sni: {domain}',
            f'alpn: [h3]'
        ]

        if obfs_type and obfs_password:
            compact_parts.extend([
                f'obfs: {obfs_type}',
                f'obfs-password: "{obfs_password}"'
            ])

        compact_parts.extend([
            f'up: {up_mbps}',
            f'down: {down_mbps}',
            f'udp: true'
        ])

        compact = f"- {{{', '.join(compact_parts)}}}"
        print(f"{compact}\n")

        # URI 格式
        print("---[ URI 格式 ]---")
        encoded_password = quote(password, safe='')
        insecure_flag = "1" if use_self_signed else "0"

        uri_params = [
            f"sni={domain}",
            f"insecure={insecure_flag}"
        ]

        if obfs_type and obfs_password:
            uri_params.extend([
                f"obfs={obfs_type}",
                f"obfs-password={quote(obfs_password, safe='')}"
            ])

        uri = f"hysteria2://{encoded_password}@{domain}:{port}?{'&'.join(uri_params)}#{quote(f'{domain}|Hysteria2', safe='')}"
        print(f"{uri}\n")

        print("=" * 46)
        print("📌 重要信息:")
        print(f"  服务器 IP: {public_ip}")
        print(f"  域名: {domain}")
        print(f"  端口: {port}")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  上行带宽: {up_mbps} Mbps")
        print(f"  下行带宽: {down_mbps} Mbps")

        if obfs_type and obfs_password:
            print(f"  QUIC 混淆: {obfs_type}")
            print(f"  混淆密码: {obfs_password}")
        else:
            print(f"  QUIC 混淆: 未启用")
        print()

        print("🔒 证书信息:")
        print(f"  证书位置: {self.cert_dir}/server.crt")
        print(f"  私钥位置: {self.cert_dir}/server.key")
        if use_self_signed:
            print(f"  类型: 自签证书 (有效期 365 天)")
        else:
            print(f"  自动续期: 已配置(acme.sh 会自动续期)\n")

        print("🎯 防火墙设置:")
        print(f"  请确保开放端口: {port}/UDP (Hysteria2 主要使用 UDP)")
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

        print("💡 Hysteria2 协议特点:")
        print("  - 基于 QUIC 协议,专为不稳定网络优化")
        print("  - 自适应带宽控制,充分利用网络资源")
        print("  - 支持 BBR 拥塞控制算法")
        print("  - 原生 UDP 支持,适合游戏和流媒体")
        if obfs_type:
            print("  - QUIC 混淆已启用,增强抗封锁能力")
        print()

        print("⚙️ 带宽说明:")
        print(f"  - 当前配置: 上行 {up_mbps} Mbps / 下行 {down_mbps} Mbps")
        print("  - 客户端会参考这些值进行速度控制")
        print("  - 建议设置为实际带宽的 80-90%")
        print("  - 可通过修改配置文件调整带宽设置\n")

        if obfs_type and obfs_password:
            print("🔐 混淆说明:")
            print(f"  - 混淆类型: {obfs_type}")
            print("  - 启用混淆后,流量特征更难被识别")
            print("  - 注意: 混淆会使服务器失去 HTTP/3 伪装能力")
            print("  - 客户端必须配置相同的混淆密码才能连接\n")

        print("📊 当前服务状态（Docker方式部署无法查看状态）:")
        try:
            sh.systemctl("status", "mihomo", "--no-pager", "-l", _fg=True)
        except:
            pass

        print("\n✅ 安装完成!请将上面的配置信息添加到您的客户端中或直接使用URI格式分享链接。")

    def install(self):
        """Hysteria2 完整安装流程"""
        try:
            print("\n" + "=" * 46)
            print("🚀 开始安装 Hysteria2")
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
            domain, email, port, username, password, up_mbps, down_mbps, obfs_type, obfs_password, use_self_signed = self.get_deployment_config()

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
            self.generate_config(port, username, password, up_mbps, down_mbps, obfs_type, obfs_password)

            # 根据部署方式执行不同操作
            if deployment_method == 'systemd':
                # 创建 systemd 服务
                self.create_systemd_service()
            else:
                # 创建并启动 Docker 容器
                self.create_docker_compose_file(self.cert_dir, self.protocol_name, port)
                self.start_docker_service(self.cert_dir)

            # 输出最终信息
            self.print_final_info(domain, port, username, password, up_mbps, down_mbps, obfs_type, obfs_password,
                                  use_self_signed)

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

    installer = HysteriaInstaller()
    installer.install()