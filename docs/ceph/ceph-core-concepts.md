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