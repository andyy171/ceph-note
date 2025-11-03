*Triển khai Ceph 4-node cơ bản *
# Tổng quan hạ tầng triển khai 
> Cụm **Ceph Reef (v18.x)** được triển khai trên **4 node ảo hóa** (host1–host4) chạy **Ubuntu Server 22.04**, sử dụng công cụ **`cephadm`** để cài đặt và quản lý các daemon containerized.
> 
> 
> Cụm này được thiết kế nhằm mục tiêu **thực hành và kiểm thử** các dịch vụ chính của Ceph bao gồm **MON, MGR, OSD, MDS, RGW và Grafana**, trong phạm vi **môi trường lab nội bộ**.
> 
> Tất cả node có cấu hình tương đồng (2 vCPU, 6GB RAM, 1 SSD 40GB, 1 HDD 60GB) và được kết nối trong cùng mạng nội bộ **192.168.xx.0/24**.
>

<img src="/images/deployment/ceph 4-node cluster/ceph 4-node cluster.png">

# Vai trò và cấu hình phần cứng của các node 
| **Hostname** | **Vai trò chính** | **CPU/RAM** | **Disk layout** | **Ghi chú** |
| --- | --- | --- | --- | --- |
| ceph-node01 | MON, MGR, OSD, MDS | 2 vCPU / 6GB | SSD 40GB (OS+meta), HDD 60GB (OSD1) | Bootstrap node |
| ceph-node02 | MON, OSD | 2 vCPU / 6GB | SSD 40GB, HDD 60GB | Gateway node |
| ceph-node03 | MON, OSD | 2 vCPU / 6GB | SSD 40GB, HDD 60GB | Gateway node |
| ceph-node04 | RGW, MDS | 2 vCPU / 6GB | SSD 40GB, HDD 60GB | CephFS node |

# Thiết kế mạng
<img src="/images/deployment/ceph 4-node cluster/ceph 4-node cluster - network.png">

| **Hostname** | **Giao diện** | **Kiểu mạng** | **Địa chỉ IP** | **Mục đích sử dụng** |
| --- | --- | --- | --- | --- |
| ceph-node01–04 | eth0 | NAT | DHCP | Truy cập Internet, tải container images, cập nhật hệ thống |
| ceph-node01–04 | eth1 | Host-only | 192.168.xx.0/24 | Mạng Ceph dùng chung cho public & cluster traffic |

# Các bước triển khai 
## Cấu hình hostname của các node
```bash
sudo hostnamectl set-hostname ceph-node01  # trên node01
sudo hostnamectl set-hostname ceph-node02  # trên node02  
sudo hostnamectl set-hostname ceph-node03  # trên node03
sudo hostnamectl set-hostname ceph-node04  # trên node04

# Cập nhật /etc/hosts
sudo tee -a /etc/hosts << EOF
192.168.xx.101 ceph-node01
192.168.xx.102 ceph-node02
192.168.xx.103 ceph-node03
192.168.xx.104 ceph-node04
EOF

# Kiểm tra hostname
hostname -f

```
<img src="/images/deployment/ceph 4-node cluster/hostname-setup.png">

## Cấu hình IP trên các node 

**Vô hiệu hóa cloud-init quản lý mạng**: Tạo file `99-disable-network-config.cfg` để ngăn cloud-init tự động tạo cấu hình mạng.

```bash
sudo nano /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg

## Thêm nội dung 
network: {config: disabled}
```
<img src="/images/deployment/ceph 4-node cluster/disable-cloud-init.png">

**Xóa cấu hình mạng cũ**: Loại bỏ các file mạng do cloud-init hoặc hệ thống tạo ra trước đó.

```bash
## Xóa các file do cloud-init sinh ra
sudo rm -f /etc/netplan/50-cloud-init.yaml
sudo rm -f /etc/netplan/90-installer-network.yaml
sudo cloud-init clean --logs
```
<img src="/images/deployment/ceph 4-node cluster/remove-cloud-init-setup.png">

Tạo cấu hình Netplan mới
<img src="/images/deployment/ceph 4-node cluster/check-network-address.png">

```bash
## Tạo lại file `01-netcfg.yaml` mới trong `/etc/netplan/`
sudo nano /etc/netplan/01-netcfg.yaml

# Cấu hình IP Tĩnh
# /etc/netplan/01-netcfg.yaml
network:
  version: 2
  ethernets:
    ens33:       # NIC1: NAT (Internet)
      dhcp4: true
    ens34:       # NIC2: Host-only (Cluster network)
      dhcp4: no
      addresses:
        - 192.168.xx.101/24
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
#
```
**Đảm bảo file cấu hình có quyền bảo mật phù hợp và kích hoạt ngay lập tức.**
```bash
# Đặt lại quyền hạn cho file `01-netcfg.yaml`
sudo chmod 600 /etc/netplan/01-netcfg.yaml
sudo chown root:root /etc/netplan/01-netcfg.yaml

# Áp dụng thay đổi
sudo netplan generate
sudo netplan apply
```
<img src="/images/deployment/ceph 4-node cluster/approved-config.png">

**Kiểm tra kết nối đến các máy khác trong mạng :**
```bash
# Sau thay đổi thì ping lại các node với nhau
ping -c2 ceph-node0
```
<img src="/images/deployment/ceph 4-node cluster/node-to-node-ping.png">

## Thêm ổ đĩa và tắt swap 
- Thêm ổ đĩa thứ 2 trên các VMs sau đó reboot
- Ping các VMs sau khi reboot để đảm bảo các cấu hình network không bị đặt lại sau khi reboot
- Tắt swap và kiểm tra xem disk đã nhận chưa rồi tẩy sạch disk 

<img src="/images/deployment/ceph 4-node cluster/disk-added-check.png">

## Cài đặt các package 

```bash
```bash
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip vim htop lvm2 net-tools chrony curl openssh-server

# Install Docker
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io ceph-common

# Check
sudo docker version
sudo docker info
```

## Setup Firewall

```bash
# Cài đặt nếu chưa có 
sudo apt install -y ufw

# Kiểm tra trạng thái
sudo ufw status verbose

## Reset về trạng thái mặc định nếu trước đó có setup
sudo ufw --force reset

# Mặc định deny tất cả inbound, allow outbound
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Cho phép SSH quản trị
sudo ufw allow 22/tcp comment 'SSH Access'

# --- Các cổng Ceph cần mở ---
# Monitor (MON)
sudo ufw allow 6789/tcp comment 'Ceph MON'

# Manager (MGR Dashboard + MGR module)
sudo ufw allow 8443/tcp comment 'Ceph MGR Dashboard'
sudo ufw allow 9283/tcp comment 'Ceph MGR Prometheus metrics'

# OSD
sudo ufw allow 6800:7300/tcp comment 'Ceph OSDs'

# Ceph REST API
sudo ufw allow 5000/tcp comment 'Ceph REST API'

# CephRGW
sudo ufw allow 7480/tcp comment 'Ceph RGW'

# MON quorum and node exporter
sudo ufw allow 3300/tcp comment 'Ceph MON quorum'
sudo ufw allow 9100/tcp comment 'Node exporter metrics (nếu dùng Prometheus)'

# Cluster network 
sudo ufw allow from 192.168.xx.0/24 comment 'Cluster network traffic'

# Cephadm SSH (quản lý container)
sudo ufw allow from 192.168.xx.0/24 to any port 22 proto tcp comment 'Cephadm SSH internal'

# Enable và kiểm tra
sudo ufw enable
sudo ufw status verbose
```
<img src="/images/deployment/ceph 4-node cluster/firewall-setup.png">


### Đồng bộ thời gian 
<img src="/images/deployment/ceph 4-node cluster/time-sync.png">


## Cấu hình SSH keyless cho root
```bash
# Tạo ssh key trên node01 (lưu ý: dùng đường dẫn tuyệt đối đến /root/.ssh)
sudo mkdir -p /root/.ssh
sudo ssh-keygen -t ed25519 -N "" -f /root/.ssh/id_ed25519
# Nếu cần tương thích ngược, chỉ tạo RSA thay cho ED25519
# sudo ssh-keygen -t rsa -b 4096 -N "" -f /root/.ssh/id_rsa

# Quyền thư mục / file -node 1
sudo chown root:root /root/.ssh
sudo chmod 700 /root/.ssh
sudo chmod 600 /root/.ssh/id_ed25519
sudo chmod 644 /root/.ssh/id_ed25519.pub

# Tạm bật password root (nếu cần) để dễ thao tác rồi tắt sau khi xác nhận keyless
# (chỉ chạy nếu bạn chưa set password root)
sudo passwd root

# Cho phép root login bằng password (tạm thời trên cả 3 node)
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Copy public key tới các node (gộp 1 lần, chỉ dùng id_ed25519.pub) - node01
sudo ssh-copy-id -i /root/.ssh/id_ed25519.pub root@ceph-node01
sudo ssh-copy-id -i /root/.ssh/id_ed25519.pub root@ceph-node02
sudo ssh-copy-id -i /root/.ssh/id_ed25519.pub root@ceph-node03

# Kiểm tra keyless login
ssh -o StrictHostKeyChecking=no root@ceph-node02 'hostname -f; whoami'
ssh -o StrictHostKeyChecking=no root@ceph-node03 'hostname -f; whoami'

# Sau khi xác nhận keyless hoạt động: vô hiệu hoá password authentication (tất cả node)
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Kiểm tra trạng thái thời gian / đồng bộ
timedatectl status
sudo systemctl status chrony
```

<img src="/images/deployment/ceph 4-node cluster/keyless-root-check.png">


# Bootstrap Cluster 
```bash
# Tải cephadm phiên bản ổn định mới nhất
echo "deb [signed-by=/usr/share/keyrings/ceph-archive-keyring.gpg] https://download.ceph.com/debian-reef jammy main" | sudo tee /etc/apt/sources.list.d/ceph.list

curl -fsSL https://download.ceph.com/keys/release.asc | gpg --dearmor | sudo tee /usr/share/keyrings/ceph-archive-keyring.gpg >/dev/null

# Cài đặt dependencies cho cephadm
sudo apt update
sudo apt install -y cephadm

# Bootstrap với các tuỳ chọn an toàn
sudo cephadm bootstrap /
    --mon-ip 192.168.xx.101 /
    --initial-dashboard-user admin /
    --initial-dashboard-password admin123 /
    --allow-fqdn-hostname /
    --cluster-network 192.168.xx.0/24

## Thêm alias 
echo "alias ceph='sudo cephadm shell -- ceph'" >> ~/.bashrc
echo "alias rados='sudo cephadm shell -- rados'" >> ~/.bashrc
echo "alias rbd='sudo cephadm shell -- rbd'" >> ~/.bashrc
echo "alias cephsh='sudo cephadm shell'" >> ~/.bashrc
source ~/.bashrc

# KIỂM TRA sau bootstrap
ceph -s
ceph status
ceph orch host ls

# Cấu hình mạng public
ceph config set global public_network 192.168.xx.0/24

# Kết nối các node
ceph cephadm get-pub-key > /tmp/ceph.pub
sudo ssh-copy-id -f -i /tmp/ceph.pub root@ceph-node02
sudo ssh-copy-id -f -i /tmp/ceph.pub root@ceph-node03
sudo ssh-copy-id -f -i /tmp/ceph.pub root@ceph-node04

# Kiểm tra lại kết nối (từ node01):
ssh root@ceph-node02 hostname
ssh root@ceph-node03 hostname
ssh root@ceph-node04 hostname

# Thêm các node vào cluster
ceph orch host add ceph-node02 192.168.xx.102
ceph orch host add ceph-node03 192.168.xx.103  
ceph orch host add ceph-node04 192.168.xx.104

# Kiểm tra tổng thể
ceph orch host ls
ceph -s

# Disable các cảnh báo ban đầu
ceph config set global mon_warn_on_insecure_global_id_reclaim false
ceph config set global mon_warn_on_insecure_global_id_reclaim_allowed false
```

<img src="/images/deployment/ceph 4-node cluster/ceph-bootstrap.png">


## Triển khai các dịch vụ 

### MON

```bash
ceph orch apply mon --placement "ceph-node01,ceph-node02,ceph-node03"

# Check
ceph mon stat
```
<img src="/images/deployment/ceph 4-node cluster/MON-added.png">

### MGR

```bash
ceph orch apply mgr --placement "ceph-node01,ceph-node02,ceph-node03"

# Check 
ceph mgr module ls
```
<img src="/images/deployment/ceph 4-node cluster/MGR-added.png">

### OSD

```bash
ceph orch device ls
ceph orch apply osd --all-available-devices
ceph osd tree

# Check 
ceph orch ps
ceph orch host ls

```
<img src="/images/deployment/ceph 4-node cluster/OSD-added.png">

# Kiểm tra cluster
```bash
ceph -s
ceph status
ceph orch host ls
```
<img src="/images/deployment/ceph 4-node cluster/ceph-cluster-check.png">

<img src="/images/deployment/ceph 4-node cluster/ceph-dashboard-1.png">

<img src="/images/deployment/ceph 4-node cluster/ceph-dashboard-2.png">



