# Triển khai Ceph 4-node
## Chuẩn bị môi trường 
### Setup Hostname

Thực hiện trên **cả 4 node** (`ceph-node01`, `ceph-node02`, `ceph-node03`, `ceph-node04`)

```bash
sudo hostnamectl set-hostname ceph-node01  # trên node01
sudo hostnamectl set-hostname ceph-node02  # trên node02  
sudo hostnamectl set-hostname ceph-node03  # trên node03
sudo hostnamectl set-hostname ceph-node04  # trên node04

# Cập nhật /etc/hosts
sudo tee -a /etc/hosts << EOF
192.168.56.101 ceph-node01
192.168.56.102 ceph-node02
192.168.56.103 ceph-node03
192.168.56.104 ceph-node04
EOF

# Kiểm tra hostname
hostname -f

```

### Setup Network

**Cấu hình IP**  

Trên các node : 

```bash
sudo nano /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg

## Thêm nội dung 
network: {config: disabled}
## Xóa các file do cloud-init sinh ra
sudo rm -f /etc/netplan/50-cloud-init.yaml
sudo rm -f /etc/netplan/90-installer-network.yaml
sudo cloud-init clean --logs
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
        - 192.168.56.101/24
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
#
# Đặt lại quyền hạn cho file `01-netcfg.yaml`
sudo chmod 600 /etc/netplan/01-netcfg.yaml
sudo chown root:root /etc/netplan/01-netcfg.yaml

# Áp dụng thay đổi
sudo netplan generate
sudo netplan apply

# Sau thay đổi thì ping lại các node với nhau
ping -c2 ceph-node0
```

### Setup ổ đĩa phụ và tắt swap

```bash
# Thêm 1 hard disk phụ trên mỗi node 
# Disable swapoff
sudo swapoff -a
sudo sed -i.bak -r 's|(^[^#].*swap.*)|#\1|' /etc/fstab

# Kiểm tra xem disk đã nhận chưa 
lsblk

# Tẩy sạch disk 
sudo wipefs -a /dev/sdb
sudo sgdisk --zap-all /dev/sdb
```

### Cài đặt Package

Thực hiện trên các node :

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

### Setup Firewall

Áp dụng tất cả các node :

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
sudo ufw allow from 192.168.56.0/24 comment 'Cluster network traffic'

# Cephadm SSH (quản lý container)
sudo ufw allow from 192.168.56.0/24 to any port 22 proto tcp comment 'Cephadm SSH internal'

# Enable và kiểm tra
sudo ufw enable
sudo ufw status verbose
```

### Setup NTP ( Network Time Protocol ) - Đồng bộ thời gian

```bash
# Đồng bộ thời gian chính xác
sudo systemctl enable --now docker chrony ssh
```

### **Cấu hình SSH keyless for root**

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

## Bootstrap Ceph Cluster 

Trên Node chính ( Node 1)  :

```bash
# Tải cephadm phiên bản ổn định mới nhất
echo "deb [signed-by=/usr/share/keyrings/ceph-archive-keyring.gpg] https://download.ceph.com/debian-reef jammy main" | sudo tee /etc/apt/sources.list.d/ceph.list

curl -fsSL https://download.ceph.com/keys/release.asc | gpg --dearmor | sudo tee /usr/share/keyrings/ceph-archive-keyring.gpg >/dev/null

# Cài đặt dependencies cho cephadm
sudo apt update
sudo apt install -y cephadm

# Bootstrap với các tuỳ chọn an toàn
sudo cephadm bootstrap \
    --mon-ip 192.168.56.101 \
    --initial-dashboard-user admin \
    --initial-dashboard-password admin123 \
    --allow-fqdn-hostname \
    --cluster-network 192.168.56.0/24

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
ceph config set global public_network 192.168.56.0/24

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
ceph orch host add ceph-node02 192.168.56.102
ceph orch host add ceph-node03 192.168.56.103  
ceph orch host add ceph-node04 192.168.56.104

# Kiểm tra tổng t
ceph orch host ls
ceph -s

# Disable các cảnh báo ban đầu
ceph config set global mon_warn_on_insecure_global_id_reclaim false
ceph config set global mon_warn_on_insecure_global_id_reclaim_allowed false
```


## Triển khai dịch vụ Ceph 

### MON

```bash
ceph orch apply mon --placement "ceph-node01,ceph-node02,ceph-node03"

# Check
ceph mon stat
```

### MGR

```bash
ceph orch apply mgr --placement "ceph-node01,ceph-node02,ceph-node03"

# Check 
ceph mgr module ls
```

### OSD

```bash
ceph orch device ls
ceph orch apply osd --all-available-devices
ceph osd tree

# Check 
ceph orch ps
ceph orch host ls

```

## Làm việc với Pool

### Lệnh tạo pool

**Công thức :**

```bash
ceph osd pool create <pool-name> <pg-num> <pgp-num> [type] [crush-ruleset-name]
```

Trong đó : 

- `<pool-name>` phải là duy nhất
- `<pg-num>`: Tổng số placement groups (nhóm vị trí) cho pool này. Số lượng PG ảnh hưởng đến hiệu năng và cách dữ liệu được phân tán.
- `<pgp-num>`: Số lượng placement groups cho mục đích placement. Thông thường, `pgp-num` bằng với `pg-num`.
    - [type] (tùy chọn): Chỉ định loại pool bạn muốn tạo .
        - Phổ biến nhất là replicated (Pool được nhân bản, yêu cầu nhiều dung lượng hơn nhưng hỗ trợ tất cả các hoạt động của Ceph)
        - và erasure(Pool sử dụng kỹ thuật erasure coding, yêu cầu ít dung lượng lưu trữ hơn nhưng chỉ hỗ trợ một tập hợp con các hoạt động có sẵn)
    - [crush-ruleset-name] (tùy chọn): Tên của bộ quy tắc CRUSH (CRUSH rule set) sẽ được sử dụng để định vị các dữ liệu trong pool. Nếu không chỉ định, Ceph sẽ **sử dụng bộ quy tắc CRUSH mặc định.**

Ví dụ : 

```bash
# tạo pool tên testpool với 32 PG
ceph osd pool create testpool 32

# Gắn ứng dụng RADOS cho pool

ceph osd pool application enable testpool rados

# Kiểm tra 
ceph osd pool ls detail
ceph osd pool get testpool all
ceph osd pool get testpool size
ceph osd pool get testpool pg_num
ceph osd pool stats
```

### Tạo pool cho các ứng dụng khác nhau

```bash
# RADOS
ceph osd pool application enable testpool rados

# RBD 
## KHÔNG dùng lệnh application enable cho RBD
rbd pool init testpool

# Các ứng dụng khác
# CephFS (nếu dùng pool cho metadata/data)
ceph osd pool application enable myfs-metadata cephfs
ceph osd pool application enable myfs-data cephfs

# RGW (Object Storage)
ceph osd pool application enable .rgw.root rgw
```

### **Thao tác Object cơ bản với RADOS**

```bash
# CRUD
## Tạo object từ file
echo "hello ceph" > /tmp/hello.txt
rados -p testpool put myobj /tmp/hello.txt

## List objects
rados -p testpool ls

## Đọc object
rados -p testpool get myobj /tmp/hello-rcvd.txt
cat /tmp/hello-rcvd.txt

## Xóa object
rados -p testpool rm myobj

# Benchmark
## Write benchmark (giữ lại objects)
rados bench -p testpool 10 write --no-cleanup

## Sequential read benchmark
rados bench -p testpool 10 seq

## Random read benchmark  
rados bench -p testpool 10 rand

## Cleanup sau benchmark
rados -p testpool cleanup

# MONITOR
## Kiểm tra pool details
ceph osd pool get testpool size
ceph osd pool get testpool pg_num
ceph osd pool stats

## Theo dõi PG status
ceph pg stat
ceph pg dump | grep testpool
ceph health detail
```

**Ví dụ 1 flow triển khai** 

```bash
# BƯỚC 1: Tạo pool
ceph osd pool create testpool 32

# BƯỚC 2: Khởi tạo cho use case cụ thể
rbd pool init testpool          # Nếu dùng cho RBD
# HOẶC
ceph osd pool application enable testpool rados  # Nếu dùng object trực tiếp

# BƯỚC 3: Kiểm tra
ceph osd pool ls detail
ceph osd pool get testpool all

# BƯỚC 4: Sử dụng (tùy use case)
# - Object operations (rados put/get) HOẶC
# - RBD operations (rbd create) HOẶC  
# - Benchmark testing

# BƯỚC 5: Monitoring
ceph pg stat
ceph osd pool stats
```

### Lưu ý

<aside>
❕

- `rbd pool init` ← Dành cho RBD
- `ceph osd pool application enable` ← Dành cho các ứng dụng khác (rados, cephfs, rgw)
- **Mỗi pool chỉ nên có MỘT application, không enable nhiều application trên cùng pool**
</aside>

### CRUSH rule

```bash
# Tạo Replicated Rule

ceph osd crush rule create-replicated <rule-name> <root> <failure-domain> [<class>]
```

Trong đó : 

- `<rule-name>`: Tên của rule (duy nhất trong cluster)
- `<root>`: Tên CRUSH root bucket (thường là 'default')
- `<failure-domain>`: Cấp độ failure domain (ví dụ: host, rack, datacenter)
- `[<class>]` (tùy chọn): Device class (ví dụ: ssd, hdd, nvme)

ví dụ : 

```bash
ceph osd crush rule create-replicated my_rule default host
ceph osd crush rule create-replicated ssd_rule default host ssd
```

```bash
# Tạo Erasure Coded Rule
ceph osd crush rule create-erasure <rule-name> [<profile>]
```

Trong đó: 

- `<rule-name>`: Tên của rule
- `[<profile>]` (tùy chọn): Tên erasure code profile (mặc định là 'default')

Ví dụ : 

```bash
ceph osd crush rule create-erasure my_ec_rule
ceph osd crush rule create-erasure my_ec_rule my_ec_profile
```

```bash
# Liệt kê Rules
ceph osd crush rule ls

# Xem chi tiết Rule
ceph osd crush rule dump [<rule-name>]  //Tên rule cụ thể, nếu không có sẽ dump tất cả.

# Xóa Rule
ceph osd crush rule rm <rule-name>

# Áp dụng Rule cho Pool
ceph osd pool set <pool-name> crush_rule <rule-name>

# Tạo CRUSH Bucket
ceph osd crush add-bucket <bucket-name> <type>  // datacenter, rack, host

#  Di chuyển Bucket
ceph osd crush move <bucket-name> <parent=bucket-name>

```

```bash

# Gán OSD vào Bucket
ceph osd crush set <osd-id> <weight> [<bucket-type>=<bucket-name> ...] [<osd-id> ...]
```

Trong đó : 

- `<osd-id>`: ID của OSD
- `<weight>`: Trọng số của OSD (thường là dung lượng TB)
- `[<bucket-type>=<bucket-name> ...]`: Vị trí trong CRUSH hierarchy

Ví dụ : `ceph osd crush set osd.0 1.0 host=node1 rack=rack1 root=default`

```bash
# Thiết lập Device Class cho OSD
 ceph osd crush set-device-class <class> <osd-name> [<osd-name> ...]
 
 eg: ceph osd crush set-device-class ssd osd.0 osd.1 osd.2
 
# Liệt kê Device Class
 ceph osd crush class ls

# Xem CRUSH Tree
ceph osd tree

# Xem CRUSH Map dưới dạng JSON
ceph osd crush dump

# Chỉnh sửa CRUSH Map bằng tay
ceph osd getcrushmap -o <compiled-crushmap-file>
crushtool -d <compiled-crushmap-file> -o <decompiled-crushmap-file>

## Chỉnh sửa file text
vi <decompiled-crushmap-file>

## Compile và apply lại
crushtool -c <decompiled-crushmap-file> -o <new-compiled-crushmap-file>
ceph osd setcrushmap -i <new-compiled-crushmap-file>

eg: 

# Tạo rule cho SSD ở failure domain host
ceph osd crush rule create-replicated ssd_rule default host ssd

# Tạo rule cho HDD ở failure domain rack
ceph osd crush rule create-replicated hdd_rule default rack hdd

# Tạo pool và áp dụng rule
ceph osd pool create ssd_pool 64 64
ceph osd pool set ssd_pool crush_rule ssd_rule

ceph osd pool create hdd_pool 128 128
ceph osd pool set hdd_pool crush_rule hdd_rule
```

### RBD

```bash
# Quản lý Image Cơ bản
## Tạo image
rbd create --size 1024 testpool/myimage

## List images trong pool
rbd ls testpool
rbd ls -l testpool  # với details

## Xem thông tin image
rbd info testpool/myimage

## Resize image
rbd resize --size 2048 testpool/myimage

## Xóa image
rbd rm testpool/myimage

# Snapshot & Clone
## Tạo snapshot
rbd snap create testpool/myimage@snap1

## List snapshots
rbd snap ls testpool/myimage

## Rollback snapshot
rbd snap rollback testpool/myimage@snap1

## Clone snapshot thành image mới
rbd clone testpool/myimage@snap1 testpool/myclone

## Xóa snapshot
rbd snap rm testpool/myimage@snap1

# Map/Unmap để sử dụng
## Map image thành block device
rbd map testpool/myimage

## Xem mapped devices
rbd showmapped

## Unmap device
rbd unmap /dev/rbd0
```

```bash
# SAMPLE WORKFLOW
# 1. Tạo pool cho RBD
ceph osd pool create rbd_pool 32 32
rbd pool init rbd_pool

# 2. Tạo và sử dụng image
rbd create --size 1024 rbd_pool/myvm_disk
rbd map rbd_pool/myvm_disk
mkfs.xfs /dev/rbd0
mount /dev/rbd0 /mnt
```

### CephFS

```bash
# Tạo và Quản lý Filesystem
## Tạo CephFS (tự động tạo metadata + data pools)
ceph fs volume create myfs

## Xem filesystems
ceph fs ls
ceph fs status

## Xóa filesystem
ceph fs volume rm myfs --yes-i-really-mean-it

# Tạo và Quản lý Filesystem
## Kernel client (recommended)
mount -t ceph :/ /mnt/cephfs -o name=admin,secret=<key>

## FUSE client
ceph-fuse /mnt/cephfs

## Unmount
umount /mnt/cephfs

## Lấy key cho mount
ceph auth get-key client.admin
```

```bash
# SAMPLE WORKFLOW
# 1. Tạo filesystem
ceph fs volume create myfs

# 2. Mount và sử dụng
mkdir /mnt/cephfs
mount -t ceph :/ /mnt/cephfs -o name=admin,secret=$(ceph auth get-key client.admin)
```

### RGW

```bash
# Triển khai RGW Service
## Deploy RGW instance
ceph orch apply rgw myrealm myzone --placement="ceph-node01"

## Kiểm tra service
ceph orch ps --daemon-type rgw

# Quản lý User & Bucket
## Tạo user
radosgw-admin user create --uid="myuser" --display-name="My User"

## List users
radosgw-admin user list

## Tạo bucket
radosgw-admin bucket create --bucket=mybucket --uid=myuser

## List buckets
radosgw-admin bucket list

#  S3 Operations với AWS CLI ( Optional ) 
## Cấu hình endpoint
aws --endpoint http://<rgw-host>:8080 s3 ls

## Tạo bucket
aws --endpoint http://<rgw-host>:8080 s3 mb s3://mybucket

## Upload file
aws --endpoint http://<rgw-host>:8080 s3 cp file.txt s3://mybucket/

## Download file
aws --endpoint http://<rgw-host>:8080 s3 cp s3://mybucket/file.txt ./

## List objects
aws --endpoint http://<rgw-host>:8080 s3 ls s3://mybucket/

# Monitoring & Troubleshooting
## Cluster status
ceph -s
ceph health detail

## OSD status
ceph osd status
ceph osd tree

## PG status
ceph pg stat

## Disk usage
ceph df
ceph df detail

## Pool usage
ceph osd pool ls detail

## Xem real-time logs
ceph -w

## Logs cho specific daemon
ceph logs <daemon-type>.<daemon-id>
ceph logs rgw.myzone.ceph-node01

# RBD Benchmark
## Map image trước
rbd map testpool/benchimage
rbd create --size 10240 testpool/benchimage

## FIO test
fio --name=randwrite --ioengine=libaio --rw=randwrite --bs=4k --numjobs=1 --size=1G --runtime=60 --time_based --group_reporting --filename=/dev/rbd0

## RADOS Benchmark
rados bench -p testpool 30 write --no-cleanup
rados bench -p testpool 30 seq
rados bench -p testpool 30 rand
```

```bash
# SAMPLE WORKFLOW
# 1. Deploy RGW
ceph orch apply rgw myobjectstore --placement="1"

# 2. Tạo user và test
radosgw-admin user create --uid=testuser --display-name="Test User"
# Lấy access_key và secret_key từ output
aws --endpoint http://<node-ip>:8080 s3 mb s3://testbucket
```

# Security - Triển khai bảo mật

---

### Tạo User riêng biệt để thao tác trong môi trường
```bash
# Tạo user Ceph chuyên dụng
sudo useradd -m -s /bin/bash ceph-operator
sudo usermod -aG ceph ceph-operator

# Tạo keyring với limited capabilities  
sudo ceph auth get-or-create client.operator \
    mon 'allow r' \
    osd 'allow rw pool=testpool' \
    mgr 'allow r' \
    -o /home/ceph-operator/ceph.client.operator.keyring

# Set permissions đúng chuẩn
sudo chown ceph-operator:ceph-operator /home/ceph-operator/ceph.client.operator.keyring
sudo chmod 600 /home/ceph-operator/ceph.client.operator.keyring

# Chuyển sang user operator để thao tác
sudo su - ceph-operator
```

