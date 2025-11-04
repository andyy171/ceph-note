# Các khái niệm cốt lõi của Ceph 
## Các loại lưu trữ (Object, Block, File)
Ceph hỗ trợ ba loại lưu trữ chính, mỗi loại phục vụ mục đích khác nhau nhưng đều dựa trên nền tảng RADOS. 

- **Object Storage (Lưu Trữ Đối Tượng)**:
    
    Dữ liệu được lưu dưới dạng **đối tượng (objects)**, mỗi đối tượng là một "hộp" chứa dữ liệu và metadata (như kích thước, ngày tạo). Không có cấu trúc thư mục như hệ thống file thông thường. Dữ liệu được phân mảnh và sao chép để đảm bảo an toàn, phù hợp cho dữ liệu lớn như ảnh, video trên cloud (hỗ trợ S3 API).
    
    <aside>
    ❕Chỉ đọc/ghi toàn bộ object, không hỗ trợ truy cập ngẫu nhiên.
    
    </aside>
    
- **Block Storage (Lưu Trữ Khối)**:
    
    Dữ liệu được chia thành các **khối (blocks)** cố định (như 4KB), hoạt động như ổ cứng ảo. Sử dụng RBD (RADOS Block Device) images, có thể mount như ổ đĩa cho máy ảo (VM). Dữ liệu được phân tán qua cluster để chịu lỗi. 
    
    <aside>
    ❕Tối ưu cho ứng dụng cần truy cập ngẫu nhiên (như database), khác với object vì không có metadata phong phú.
    
    </aside>
    
- **File Storage (Lưu Trữ Tệp)**:
    
    Cung cấp hệ thống file với cấu trúc thư mục và file, tương tự ext4. Sử dụng CephFS, dữ liệu file được phân mảnh thành objects, metadata được quản lý bởi MDS (Metadata Server). 
    
    <aside>
    ❕Hỗ trợ cấu trúc cây thư mục, phù hợp cho chia sẻ file nhóm, phức tạp hơn block do cần quản lý metadata.
    
    </aside>

## Các thành phần của Ceph
### RADOS (Reliable Autonomic Distributed Object Store)
- Lớp lưu trữ cốt lõi của Ceph, quản lý tất cả dữ liệu dưới dạng objects.
- RADOS tự động phân tán dữ liệu qua các OSD, sao chép để chịu lỗi và tự sửa chữa (autonomic) khi có sự cố.

### **CRUSH (Controlled Replication Under Scalable Hashing)**
- Thuật toán phân bổ dữ liệu thông minh, quyết định vị trí lưu trữ mà không cần bảng tra cứu trung tâm.
- Sử dụng hàm hash để ánh xạ dữ liệu vào OSD dựa trên cấu trúc cluster (rack, host). Hỗ trợ replication hoặc erasure coding. Khi thêm/xóa node, CRUSH tự cân bằng dữ liệu.
- CRUSH Rule là định nghĩa **cách dữ liệu được placement** across cluster
    - Thường có 2 kiểu là **Replicated Rules và Erasure Coded Rules ( dành cho** EC pools giúp tiết kiệm dung lượng)

### OSD (Object Storage Daemon)
- Tiến trình chạy trên mỗi đĩa lưu trữ vật lý, quản lý đọc/ghi objects trên đĩa.
- OSD báo cáo trạng thái (up/down) cho cluster, xử lý replication và kiểm tra lỗi (scrubbing).

### PG (Placement Group)
- Nhóm logic chứa 100-1000 objects, giúp phân tán dữ liệu mịn hơn OSD.
- CRUSH ánh xạ PG vào các OSD (ví dụ: 3 replicas trên 3 OSD). Nếu OSD hỏng, PG được di chuyển để duy trì redundancy.

### Pool
- Nhóm logic chứa nhiều PG, định nghĩa chính sách lưu trữ (replication size, crush rule).
- Mỗi pool có ID riêng, dùng cho object/block/file. Ceph tự tạo PG khi tạo pool.

### MON (Monitor)
- Theo dõi trạng thái cluster, duy trì cluster map (bản đồ vị trí dữ liệu).
- Nhóm MON (3-5 node) dùng Paxos để đồng bộ

### MGR (Manager)
- Cung cấp dashboard, telemetry và tích hợp với hệ thống bên ngoài (như Kubernetes).
- Chạy song song MON, xử lý thống kê và báo cáo.

### **MDS (Metadata Server)**
- Quản lý metadata cho CephFS (file storage), như cấu trúc thư mục, quyền truy cập.
- Phân tán metadata qua nhiều MDS để chịu lỗi.

### **RGW (RADOS Gateway)**
- Cổng giao tiếp cho object storage qua API (S3/Swift).
- Chuyển request từ client thành RADOS operations.

### **FileStore**
- Backend cũ, lưu objects như file trong filesystem (ext4/XFS).
- Metadata và dữ liệu tách biệt, dùng journal để ghi nhanh. Tuy nhiên, overhead cao do tầng filesystem.
- Dễ debug, nhưng chậm với dữ liệu lớn.

### **BlueStore**
- Backend mặc định, lưu trực tiếp trên block device, không qua filesystem.
- Sử dụng RocksDB cho metadata, BlueFS cho journal/WAL, hỗ trợ compression và checksum.
- Nhanh hơn 30-50%, tiết kiệm RAM, nhưng phức tạp khi troubleshoot.

### Cluster Maps
Cluster maps là "GPS" giúp client và OSD biết vị trí dữ liệu. MON duy trì và phân phối.

- **OSD Map**: Liệt kê tất cả OSD (ID, trạng thái up/in).
    
    **Cơ chế vận hành**: Cập nhật khi OSD join/leave.
    
- **CRUSH Map**: Định nghĩa cấu trúc cluster (host, rack) và rule phân bổ.
    
    **Cơ chế vận hành**: Dùng để tính vị trí PG.
    
- **PG Map**: Vị trí từng PG (OSD nào là primary/replicas).
    
    **Cơ chế vận hành**: Giúp client đọc/ghi trực tiếp OSD mà không qua MON.
    
    **Ví dụ**: OSD Map như danh sách địa điểm, CRUSH Map như tuyến đường.

### Paxos & Quorum
- **Paxos**: Thuật toán đồng thuận để MON/MGR/MDS thống nhất trạng thái (như OSD up/down).
    
    **Cơ chế vận hành**: Leader đề xuất, node vote; chịu lỗi nếu <50% hỏng. Phiên bản mới dùng Raft đơn giản hơn.
    
    **Ví dụ**: Như bỏ phiếu bầu chủ tịch, cần đa số đồng ý.
    
- **Quorum**: Số node tối thiểu để đưa ra quyết định hợp lệ (thường >50%).
    
    **Cơ chế vận hành**: Ngăn split-brain (cluster chia đôi).
    
    **Ví dụ**: Như tòa án cần đa số thẩm phán để phán quyết.

### CephX Authentication Model
- **CephX** là **cơ chế xác thực nội bộ của Ceph**, được thiết kế tương tự **Kerberos** nhằm đảm bảo mọi giao tiếp giữa client và daemon đều được **xác minh danh tính và bảo vệ an toàn**.
- Cơ chế hoạt động như sau: **Client gửi yêu cầu xác thực đến Monitor (MON)** bằng cặp username/secret key. Nếu hợp lệ, MON **cấp một session ticket (keyring)** có thời hạn; client dùng ticket này để **ký và xác thực các yêu cầu** tới OSD, MDS hay MON khác mà không cần gửi lại mật khẩu.
- Cách làm này giống như **mua vé vào rạp**: người dùng lấy vé từ quầy (MON) rồi dùng nó để ra vào rạp (OSD). CephX giúp **ngăn truy cập trái phép**, **giảm rủi ro lộ khóa**, hỗ trợ **ACL và LDAP**, và được **kích hoạt mặc định trong mọi cụm Ceph**.

### Networking (Public vs Cluster, MTU, Bonding)
- **Public Network**: Mạng cho client truy cập (read/write).
- **Cluster Network**: Mạng nội bộ cho OSD-MON (heartbeats, replication).
    
    **Cơ chế vận hành**: Tách biệt để tăng bảo mật và hiệu suất; khuyến nghị 10Gbps+.
    
- **MTU (Maximum Transmission Unit)**: Kích thước gói tin tối đa (thường 9000 cho Jumbo frames).
    
    **Cơ chế vận hành**: Tăng MTU giảm overhead CPU, cần cấu hình toàn cluster.
    
- **Bonding**: Gộp nhiều NIC thành một logical interface (modes: active-backup, LACP).
    
    **Cơ chế vận hành**: Tăng băng thông và redundancy.
    
    **Ví dụ**: Public như đường khách, cluster như đường nội bộ; bonding như nhiều làn xe.


### Smart Daemons, Failure Domain, Reweighting
- **Smart Daemons**: Daemon tự động điều chỉnh (OSD báo full, MON tự elect leader).
    
    **Cơ chế vận hành**: Dùng agent để monitor và tự sửa.
    
- **Failure Domain**: Đơn vị chịu lỗi (rack, host, OSD) trong CRUSH map.
    
    **Cơ chế vận hành**: Đảm bảo replicas không cùng domain (như 3 replicas ở 3 rack).
    
    **Ví dụ**: Không để tất cả trứng trong một giỏ.
    
- **Reweighting**: Điều chỉnh trọng số OSD (0-1) để cân bằng dữ liệu.
    
    **Cơ chế vận hành**: Giảm weight cho OSD chậm/full, dữ liệu được di chuyển dần. Lệnh: ceph osd reweight.
    
    **Ví dụ**: Như giảm tải xe nếu bánh xe yếu.


## Librados – Thư Viện Cốt Lõi Cho Truy Cập Trực Tiếp Vào RADOS
- Librados là thư viện C++ cung cấp khả năng truy cập trực tiếp vào lớp RADOS của Ceph Storage Cluster, cho phép ứng dụng lưu trữ và lấy object mà không qua giao diện cấp cao. Librados xây dựng nền tảng mạnh mẽ, mở rộng cao, hiệu năng cao, tận dụng RADOS mà không giảm tốc độ. 
- Xuất phát từ mục tiêu lưu trữ phân tán, librados hỗ trợ mở rộng tới exabyte, tương thích cao với C, C++, Python, Java, PHP. Nó nổi bật trong ngành lưu trữ, giải pháp cho vấn đề tăng trưởng dữ liệu. 
+ Nguyên tắc cơ bản: mở rộng thành phần, chịu lỗi cao, dựa trên phần mềm mở, thích nghi cao. Librados quản lý object, nhân bản toàn cluster, nâng cao bảo đảm. Object không có đường dẫn vật lý, linh hoạt mở rộng tới petabyte-exabyte.
>Librados và tương lai lưu trữ: Khối lượng dữ liệu tăng 40-60% hàng năm, sinh vấn đề thống nhất, phân tán, hiệu năng.
>
=> Librados giải pháp nổi bật với thống nhất, phân phối, chi phí hợp lý. Tích hợp kernel, vượt trội hơn giải pháp hiện tại. 
- Librados – Giải pháp cloud: Truy cập cloud cần lưu trữ, librados giải quyết giới hạn truyền thống, hỗ trợ OpenStack, Kubernetes. Đội ngũ Canonical, Red Hat, SUSE hoàn thiện librados, tương thích Linux cao. 
- Librados – Software-defined: Tiết kiệm chi phí, hỗ trợ phần cứng đa dạng, lợi thế low cost, reliability, scalability. 
- Librados – Truy cập thống nhất: Object-based access duy nhất, đáp ứng tăng trưởng dữ liệu. Xây dựng unified access, hỗ trợ luồng dữ liệu lớn. Quản lý object, hỗ trợ mở rộng không giới hạn bằng CRUSH.

- Kiến trúc mới: Không dùng metadata trung tâm, thay bằng CRUSH tính toán vị trí data, cải thiện tốc độ, phân tán node. CRUSH nhận thức hạ tầng (disk, pool, node, rack, data center), tự sửa lỗi, nhân bản data. Tạo hạ tầng đảm bảo, đáng tin cậy. Hỗ trợ atomic transaction, interclient communication. Tăng performance, reliability cho PaaS/SaaS. 

>Librados dẫn đầu công nghệ access mới, vượt giới hạn, mở, software-defined, linh hoạt. Thống nhất object access, phù hợp small/big data. Tự quản trị, sửa lỗi disk, node, network, rack, data center.
>

## RBD – Ceph Block Device
- RBD hay Ceph Block Device là thành phần cung cấp giải pháp block storage trong Ceph, lưu trữ dữ liệu dạng khối với mở rộng, hiệu năng cao, chịu lỗi vượt trội. RBD thiết kế đáp ứng **lưu trữ phân tán, mạnh mẽ, mở rộng cao**, hỗ trợ exabyte, tương thích cao hệ thống ảo hóa phần cứng. RBD nổi bật ngành lưu trữ đám mây, giải pháp cho vấn đề cloud public private hybrid. Phần cứng quyết định hạ tầng, RBD đáp ứng, cung cấp block storage mạnh, tin cậy cao.

- RBD blocks chia thành nhiều obj, phân tán toàn Ceph cluser, cung cấp tính bảo đảm, hiệu năng cao. RBD hỗ trợ Linux kernel, và được tích hợp với Linux kernel, cung cấp tính năng snapshot tốc độ cao, nhẹ, copy-on-write cloning, and several others. Hỗ trợ in-memory caching, nâng cao hiệu năng.

- Nguyên tắc cơ bản RBD: 
+ Mở rộng thành phần, chịu lỗi cao.
+ Phần mềm mở, thích nghi cao, tương thích phần cứng. 

- Ceph RBD hỗ trợ image size tới 16EB. Image có thể là disk vật lý, máy ảo, … Các công nghệ KVM, Zen hỗ trợ đầy đẩy RBD, tăng tốc máy ảo. Ceph block hỗ trợ đầy đủ nền tảng ảo hóa mới OpenStack, CloudStack,..
+ Nền tảng RBD dựa object RADOS, tổ chức blocks objects. Dữ liệu block lưu object cluster. Block storage RBD giải pháp truyền thống, hạ tầng độc lập phần cứng. RBD quản lý object, nhân bản cluster, nâng bảo đảm. Block không đường dẫn vật lý, linh hoạt mở rộng petabyte-exabyte.

<img src="/images/theory/RBD.png">

## So sánh với block truyền thống 
- Block truyền thống không metadata thông minh. Metadata quyết định viết đọc. Cần trung tâm quản lý. Request tìm bảng metadata lớn, trễ cao hệ lớn. 
- RBD dùng CRUSH tính toán vị trí, cải thiện tốc độ. Phân tán node. CRUSH nhận thức hạ tầng disk pool node rack switch data center. Lỗi, lưu bản sao nhân rộng, data sẵn sàng. CRUSH tự quản trị sửa lỗi nhân rộng. Hơn 1 bản sao. Hạ tầng block đảm bảo. Sử dụng RBD tăng mở rộng.
RAID kết thúc: RAID ứng dụng lâu, thành công tái tạo chịu lỗi. Tới giới hạn. Dung lượng 4TB-6TB, tái tạo tốn giờ ngày tháng tài nguyên. Tăng TCO chi phí. Quan tâm disk size rpm. Hardware đắt RAID cards, không thêm dung lượng. RAID 5 chịu 1, RAID 6 2, nhiều khó khôi phục. Chỉ disk, không network hardware OS. RBD giải quyết, không phụ thuộc RAID, software-defined. Nhân bản config, định nghĩa bản sao tối ưu. Chịu lỗi nhiều hơn 2, khôi phục nhanh, không chính phụ. Lưu lượng lớn CRUSH maps.
RBD block storage: Block SAN, volumes block node. Lưu lớn đảm bảo hiệu năng. Volumes map OS filesystem. Ceph RBD bảo đảm phân phối hiệu năng block client. RBD chia obj phân tán cluster bảo đảm cao. Hỗ trợ kernel tích hợp snapshot nhanh copy-on-write cloning caching nâng hiệu năng. Image 16EB disk vật lý VM. KVM Xen hỗ trợ RBD tăng tốc VM. RBD hỗ trợ OpenStack CloudStack. RBD SAN doanh nghiệp thin provisioning copy-on-write snapshots clones revertible read-only hỗ trợ cloud.

>RBD dẫn đầu block mới. Vượt giới hạn. Mở software-defined tương thích. Giao diện linh hoạt. Mạnh RAID vượt giới hạn. Bảo đảm HA. Thống nhất toàn diện block. Phù hợp small big block không trục trặc. RBD phân tán client nhanh. Không truyền thống kỹ thuật mới tính toán động. Tăng hiệu năng. Dữ liệu tổ chức tự động. Không lo sự cố intelligent xử lý. Tự quản trị sửa lỗi. Vượt đảm bảo. Sửa disk node network rack data center geographies.
>

## CephFS – Ceph File System
- Ceph filesystem hay CephFS, là POSIX-compliant filesystem, được sử dụng trong Ceph storage cluster sử dụng để lưu trữ user data. CephFS hỗ trợ tốt Linux kernel driver, kiến CephFS tương thích tốt với các nền tảng Linux OS. CephFS lưu data và medata riêng biệt, cung cấp hiệu năng, tính bảo đảm cho app host nằm trên nó

Trong Ceph cluster, Ceph fs lib (libcephfs) chạy trên Rados library (librados) – giao thức thuộc Ceph storage - file, block, and object storage. Để sử dụng CephFS, cần ít nhất 1 Ceph metadata server (MDS) để chạy cluster nodes. Tuy nhiên, sẽ không tốt khi chỉ có 1 MDS server nó sẽ ảnh hưởng tính chịu lỗi Ceph. Khi cấu hình MDS, client có thể sử dụng CephFS theo nhiều cách. Để mount Cephfs, client cần sử dụng Linux kernel hoặc ceph-fuse (filesystem in user space) drivers provided by the Ceph community.

Bên cạnh, Client có thể sử dụng phần mềm thứ 3 như Ganesha for NFS and Samba for SMB/CIFS. Phần mềm cho phép tương tác với "libcephfs", bảo đảm lưu trữ user data phân tán trong Ceph storage cluster. CephFS có thể sử dụng cho Apache Hadoop File System (HDFS). Sử dụng libcephfs component to store data to the Ceph cluster. Để thực hiện, Ceph community cung cấp CephFS Java interface for Hadoop and Hadoop plugins. The libcephfs và librados components rất linh hoạt và ta có thể xây dựng phiên bản tùy chỉnh, tương tác với nó, xây dựng data bên dưới Ceph storage cluster.

<img src="/images/theory/cephfs.png">

## RGW – RADOS Gateway
Phương pháp lưu trữ data dạng object thay vì file, blocks truyền thống. Object-based storage nhận được nhiều sự chú ý trong storage industry.

Các tổ chức mong muốn giải pháp lưu trữ toàn diện cho lượng data khổng lồ, Ceph là giải pháp nổi bật vì nó là true object-based storage system. Ceph phân phối obj storage system, cung cấp object storage interface thông qua Ceph's object gateway, được biệt là RADOS gateway (radosgw).

RADOS gateway (radosgw) sử dụng librgw (the RADOS gateway library) và librados, cho phép app thiết lập kết nối với Ceph object storage. Ceph cung cấp giải pháp lưu trữ ổn định, và có thể truy cập thông qua RESTful API.

The RADOS gateway cung cấp RESTful interface để sử dụng cho application lưu trữ

data trên Ceph storage cluster. RADOS gateway interfaces gồm:

Swift compatibility: This is an object storage functionality for the OpenStack Swift API

S3 compatibility: This is an object storage functionality for the Amazon S3 API

Admin API: This is also known as the management API or native API, which can be used directly in the application to gain access to the storage system for management purposes

Để truy câp Ceph object storage system, ta có thể sử dụng RADOS gateway layer. librados software libraries cho phép user app truy tập trực tiếp đến Ceph = C, C++, Java, Python, and PHP. Ceph object storage has multisite capabilities, nó cung cấp giải pháp khi gặp sự cố. Các object storage configuration có thể thực hiện bởi Rados hoặc federated gateways.

<img src="/images/theory/rgw.png">

## Erasure Coding – Công nghệ Bảo vệ Dữ liệu Tiên tiến Trong Ceph

**Erasure Coding (EC)** là một kỹ thuật bảo vệ dữ liệu giúp tiết kiệm không gian lưu trữ đáng kể so với phương pháp nhân bản (Replication) truyền thống, trong khi vẫn cung cấp khả năng chịu lỗi cao. Nó là xương sống cho các hệ thống lưu trữ phân tán, mạnh mẽ và có khả năng mở rộng đến quy mô exabyte.

**Ví dụ đơn giản:** Thay vì lưu 3 bản sao của một file (tốn 3TB để lưu 1TB dữ liệu), EC "chia nhỏ" dữ liệu và tính toán thêm các phần dự phòng, giúp bạn chỉ cần dung lượng ít hơn (ví dụ: 1.5TB cho 1TB dữ liệu) mà vẫn chịu được lỗi của ổ cứng.

### Nguyên lý Hoạt động
Erasure Coding hoạt động dựa trên hai khái niệm chính:

- `k` (Data Chunks): Dữ liệu được chia thành `k` phần bằng nhau.

- `m` (Coding Chunks): Hệ thống tính toán và tạo ra `m` phần dữ liệu mã hóa (parity) từ `k` phần trên.

Cách thức:

1. Khi bạn ghi một object vào Ceph, EC sẽ chia nó thành `k` khối dữ liệu.
2. Từ `k` khối này, nó tính toán ra `m` khối mã hóa.
3. Tất cả `k + m` khối này được phân tán lưu trữ trên các ổ đĩa (OSD) khác nhau trong cluster.

- Khi xảy ra sự cố: Nếu có tối đa `m` ổ đĩa bị lỗi, hệ thống có thể sử dụng bất kỳ k khối nào còn lại (bao gồm cả data chunks và coding chunks) để tính toán và khôi phục lại toàn bộ dữ liệu gốc.

+ Ví dụ: Với cấu hình `k=4, m=2`:
* Dữ liệu được chia thành 4 phần.
* Tạo ra 2 phần parity.
* Tổng cộng 6 phần được lưu trên các OSD khác nhau.
* Hệ thống vẫn hoạt động bình thường ngay cả khi 2 OSD bất kỳ cùng lúc bị lỗi.

### Tại sao Erasure Coding lại quan trọng?
1. Tiết kiệm chi phí & Không gian
- **Hiệu suất lưu trữ cao:** So với replication (lưu 3 bản sao, overhead 200%), EC có overhead thấp hơn nhiều. Ví dụ, profile k=4, m=2 chỉ có overhead 50% (dùng 1.5GB để lưu 1GB dữ liệu).

- **Giảm TCO (Tổng chi phí sở hữu):** Bạn cần ít ổ cứng hơn để đạt được cùng một mức độ bảo vệ dữ liệu.

2. Khả năng chịu lỗi vượt trội & Mở rộng quy mô
- **Chịu lỗi linh hoạt:** Bạn có thể cấu hình để chịu được lỗi của nhiều hơn 2 ổ đĩa (ví dụ: m=3 chịu được lỗi 3 OSD), điều mà RAID truyền thống khó làm được.

- **Mở rộng đến Exabyte:** Kiến trúc phân tán giúp EC mở rộng dễ dàng, phù hợp với nhu cầu dữ liệu lớn.

3. Kiến trúc "Software-Defined"
- **Không phụ thuộc phần cứng:** EC được thực thi bằng phần mềm trong Ceph, không cần đến các card RAID đắt tiền. Nó có thể chạy trên bất kỳ phần cứng tiêu chuẩn nào.

- **Thông minh với CRUSH:** Thay vì dùng một bảng metadata tập trung để tìm dữ liệu (có thể gây nghẽn cổ chai), EC sử dụng thuật toán CRUSH để tính toán vị trí của các khối dữ liệu. Điều này giúp tăng hiệu năng và độ trễ thấp trong các hệ thống quy mô lớn. CRUSH hiểu rõ cơ sở hạ tầng (ổ đĩa, node, rack, trung tâm dữ liệu) để đảm bảo các khối được phân tán một cách an toàn.

### So sánh với Replication và RAID

### Cấu hình & Sử dụng trong Ceph

Tạo một Erasure Coded Pool
```bash
# Tạo một pool EC với profile mặc định (k=2, m=1)
ceph osd pool create my_ec_pool erasure

# Tạo pool với profile tùy chỉnh (ví dụ: k=4, m=2)
ceph osd erasure-code-profile set myprofile k=4 m=2 crush-failure-domain=host
ceph osd pool create my_custom_ec_pool erasure myprofile
```

**Lưu ý quan trọng:**
- Không sửa profile sau khi tạo pool: Hãy lên kế hoạch kỹ lưỡng trước khi tạo pool, vì bạn không thể thay đổi profile k và m sau đó.
- Cân nhắc hiệu suất: Ghi dữ liệu vào pool EC thường chậm hơn so với pool replicated vì cần nhiều thao tác tính toán và ghi.
- Một số tính năng mới (Ceph Octopus trở lên):
+ Cho phép ghi một phần (partial writes) để tối ưu hiệu suất.
+ Quá trình recovery được tối ưu, chỉ cần K shards để khôi phục.
+ Lưu ý: Tính năng Cache Tiering cho EC đã bị deprecated kể từ phiên bản Ceph Reef.

> Erasure Coding không chỉ là một sự thay thế cho Replication hay RAID, mà nó là một bước tiến công nghệ, định hình tương lai của lưu trữ phân tán. Với ưu điểm vượt trội về tiết kiệm chi phí, khả năng mở rộng và chịu lỗi linh hoạt, EC là lựa chọn hàng đầu cho các hệ thống lưu trữ đám mây và big data, nơi mà khối lượng dữ liệu tăng lên chóng mặt hàng năm.
>