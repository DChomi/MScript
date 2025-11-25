#!/usr/bin/env python3
"""
Mieru.py - Mieru 协议部署模块
继承 MihomoBase 基类,实现 Mieru 协议的具体部署
"""

import sh
import sys
import yaml
from BaseClass import MihomoBase


class MieruInstaller(MihomoBase):
    """Mieru 协议安装器"""

    def __init__(self):
        super().__init__()
        self.protocol_name = "Mieru"

    def get_deployment_config(self):
        """获取 Mieru 部署配置"""
        print("\n" + "=" * 42)
        print("⚙️ Mieru 部署配置")
        print("=" * 42 + "\n")

        # 选择传输协议
        print("📡 传输协议:")
        print("  1. TCP")
        print("  2. UDP (推荐)")

        while True:
            transport_choice = input("\n请选择传输协议 (1/2): ").strip()
            if transport_choice in ['1', '2']:
                break
            print("❌ 无效选项,请重新输入")

        transport = "TCP" if transport_choice == '1' else "UDP"

        # 获取端口
        print("\n📌 端口配置:")
        port = self.get_port_input()
        print(f"✅ 使用端口: {port}")

        # 获取用户名
        print("\n👤 用户名配置:")
        username = input("请输入用户名(留空则使用 'user1'): ").strip()

        if not username:
            username = "user1"
            print(f"✅ 使用默认用户名: {username}")
        else:
            print(f"✅ 使用自定义用户名: {username}")

        # 获取密码
        print("\n🔑 密码配置:")
        password = self.get_password_or_uuid_input(use_uuid=False, prompt_type="密码")

        # 确认配置
        print(f"\n📋 配置信息确认:")
        print(f"  传输协议: {transport}")
        print(f"  端口: {port}")
        print(f"  用户名: {username}")
        print(f"  密码: {password}\n")

        confirm = input("确认无误?(y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ 已取消")
            sys.exit(1)

        return transport, port, username, password

    def generate_config(self, transport, port, username, password):
        """生成 Mieru 配置"""
        print("⚙️ 生成 Mieru 配置...")

        # 确保配置目录存在
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        config = {
            'listeners': [
                {
                    'name': 'mieru-in-1',
                    'type': 'mieru',
                    'port': port,
                    'listen': '0.0.0.0',
                    'transport': transport,
                    'users': {
                        username: password
                    }
                }
            ]
        }

        config_file = self.cert_dir / "config.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        print("✅ 配置文件生成完成")

    def print_final_info(self, transport, port, username, password):
        """输出 Mieru 最终配置信息"""
        public_ip = self.get_public_ip()

        print("\n" + "=" * 46)
        print("✅ Mieru 部署完成!")
        print("=" * 46 + "\n")

        print("⚠️ 注意: Mieru 协议不支持分享链接")
        print("   请在客户端手动添加节点配置\n")

        print("📋 Mieru 客户端配置:\n")

        print("---[ YAML 格式 ]---")
        print(f"- name: Mieru|{transport}|{public_ip}")
        print(f"  server: {public_ip}")
        print(f"  type: mieru")
        print(f"  port: {port}")
        print(f"  transport: {transport}")
        print(f"  username: {username}")
        print(f"  password: {password}")
        print(f"  udp: true\n")

        print("=" * 46)
        print("📌 重要信息:")
        print(f"  服务器 IP: {public_ip}")
        print(f"  传输协议: {transport}")
        print(f"  端口: {port}")
        print(f"  用户名: {username}")
        print(f"  密码: {password}\n")

        print("🎯 防火墙设置:")
        print(f"  请确保开放端口: {port}")
        if transport == "TCP":
            print(f"\n  Ubuntu/Debian:")
            print(f"    sudo ufw allow {port}/tcp")
            print(f"\n  CentOS/RHEL:")
            print(f"    sudo firewall-cmd --permanent --add-port={port}/tcp")
            print(f"    sudo firewall-cmd --reload")
        elif transport == "UDP":
            print(f"\n  Ubuntu/Debian:")
            print(f"    sudo ufw allow {port}/udp")
            print(f"\n  CentOS/RHEL:")
            print(f"    sudo firewall-cmd --permanent --add-port={port}/udp")
            print(f"    sudo firewall-cmd --reload")
        print()

        print("=" * 46 + "\n")

        print("🔧 服务管理命令:")
        print("  查看状态: systemctl status mihomo")
        print("  重启服务: systemctl restart mihomo")
        print("  查看日志: journalctl -u mihomo -f")
        print("  停止服务: systemctl stop mihomo\n")

        print("=" * 46 + "\n")

        print("📖 客户端配置说明:")
        print("  1. 打开您的 Clash/Mihomo 客户端")
        print("  2. 找到配置文件或节点添加界面")
        print("  3. 手动输入上述 YAML 配置信息")
        print("  4. 或将上述 YAML 格式配置复制到配置文件中\n")

        print("=" * 46 + "\n")

        print("📊 当前服务状态（Docker方式部署无法查看状态）:")
        try:
            sh.systemctl("status", "mihomo", "--no-pager", "-l", _fg=True)
        except:
            pass

        print("\n✅ 安装完成!")
        print("⚠️ 重要提醒: Mieru 不生成分享链接,请按照上述信息手动添加节点。")

    def install(self):
        """Mieru 完整安装流程"""
        try:
            print("\n" + "=" * 46)
            print("🚀 开始安装 Mieru")
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
            transport, port, username, password = self.get_deployment_config()

            # 生成配置
            self.generate_config(transport, port, username, password)

            # 根据部署方式执行不同操作
            if deployment_method == 'systemd':
                # 创建 systemd 服务
                self.create_systemd_service()
            else:
                # 创建并启动 Docker 容器
                self.create_docker_compose_file(self.cert_dir, self.protocol_name, port)
                self.start_docker_service(self.cert_dir)

            # 输出最终信息
            self.print_final_info(transport, port, username, password)

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

    installer = MieruInstaller()
    installer.install()