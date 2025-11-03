# Tổng quan kiến trúc Ceph 
> Ceph là hệ thống lưu trữ phân tán, mã nguồn mở, được thiết kế để cung cấp giải pháp lưu trữ thống nhất (Object, Block, File) với khả năng mở rộng, độ tin cậy cao và chi phí tối ưu. Ceph phù hợp cho các môi trường cần lưu trữ dữ liệu lớn, yêu cầu tính sẵn sàng cao và không phụ thuộc vào phần cứng cụ thể.
>

## Tại sao lại cần Ceph ? 
Các hệ thống SAN (Storage Area Network) và NAS (Network Attached Storage) truyền thống thường gặp các hạn chế đáng kể. Chúng đắt đỏ, phụ thuộc vào nhà cung cấp, khó mở rộng theo kiểu scale-up và có nguy cơ điểm lỗi duy nhất (SPOF). Việc mở rộng dung lượng hoặc hiệu suất thường đi kèm chi phí cao, gây khó khăn cho doanh nghiệp.

⇒ Ceph khắc phục những hạn chế này với nhiều ưu điểm vượt trội. 

- Hệ thống sử dụng phần cứng phổ thông (commodity hardware), giúp giảm chi phí đáng kể.
- Hỗ trợ mở rộng ngang (scale-out) bằng cách ***thêm node mới mà không gián đoạn dịch vụ.***
- Cung cấp tính linh hoạt với khả năng ***hỗ trợ cả Object, Block và File storage trong một hệ thống duy nhất***.
- Thiết kế không SPOF và khả năng tự động phục hồi (self-healing) ⇒ đảm bảo độ tin cậy cao.
- Là giải pháp mã nguồn mở, Ceph không khóa người dùng vào một nhà cung cấp cụ thể và dễ dàng tùy chỉnh theo nhu cầu.
- Đặc biệt, Ceph không yêu cầu phần cứng chuyên dụng (hardware-agnostic), hoạt động hiệu quả trên các thiết bị phổ thông, giảm chi phí đầu tư.
<img src="images\theory\ceph-structure-1.png">

Ceph cung cấp giải pháp lưu trữ thống nhất cho nhiều nhu cầu khác nhau. 

- Với Object Storage, Ceph hỗ trợ lưu trữ dữ liệu không cấu trúc như ảnh, video, log thông qua giao diện S3 hoặc Swift, phù hợp cho các ứng dụng đám mây.

> Tại Ceph, Object sẽ không tồn tại đường dẫn vật lý, toàn bộ Object được quản trị dưới dạng Key Object
> 

- Về Block Storage, Ceph cung cấp block device cho máy ảo (VM) hoặc container, tích hợp tốt với OpenStack, Kubernetes.
- Đối với File Storage, CephFS hỗ trợ hệ thống tệp phân tán cho các ứng dụng cần truy cập tệp truyền thống. Các ứng dụng thực tế bao gồm lưu trữ dữ liệu IoT, backup, media streaming hoặc xây dựng cơ sở hạ tầng đám mây.

Ceph bao gồm nhiều thành phần phối hợp chặt chẽ để cung cấp hệ thống lưu trữ phân tán thống nhất. Mỗi dịch vụ đảm nhiệm một vai trò riêng, từ giám sát đến lưu trữ và truy cập dữ liệu, tạo nên một kiến trúc linh hoạt, tự phục hồi và mở rộng dễ dàng.

- **MON (Monitor)** quản lý bản đồ cụm (cluster map), theo dõi trạng thái các node và đảm bảo đồng thuận trong hệ thống bằng thuật toán Paxos. MON duy trì thông tin cấu hình và trạng thái tổng thể của cụm Ceph.
- **MGR (Manager)** cung cấp giao diện quản lý và giám sát hiệu suất, đồng thời tích hợp với các công cụ bên ngoài. MGR thường hoạt động song song với MON và cung cấp Dashboard, module thống kê, và plugin giám sát (Prometheus, Zabbix...).
- **OSD (Object Storage Daemon)** chịu trách nhiệm quản lý lưu trữ dữ liệu thực tế trên ổ đĩa, xử lý thao tác đọc/ghi, sao chép (replication), cân bằng tải, và tự phục hồi khi có lỗi. Mỗi ổ đĩa dữ liệu thường tương ứng với một OSD daemon.
- **RGW (RADOS Gateway)** cung cấp giao diện Object Storage (S3/Swift) tương thích Amazon S3 và OpenStack Swift, cho phép ứng dụng truy cập dữ liệu qua HTTP API.
- **MDS (Metadata Server)** quản lý metadata cho CephFS (Ceph File System), hỗ trợ truy cập dữ liệu dạng tệp, điều phối quyền truy cập, và tăng hiệu suất thao tác file..

## Ceph Data Flow: From Client to OSD
Trong Ceph, **dữ liệu được lưu trữ và truy cập theo một quy trình rõ ràng** từ **Client** đến **OSD (Object Storage Daemon)**. Dữ liệu được tổ chức dưới dạng **đối tượng (object)** và được phân phối trong các **pool**.
Mỗi **pool** bao gồm nhiều **Placement Group (PG)** — là các nhóm logic giúp Ceph phân tán và cân bằng dữ liệu. **Mỗi đối tượng chỉ thuộc về một PG duy nhất**, và **mỗi PG** lại được ánh xạ đến **một tập hợp OSD**, nơi dữ liệu thực tế được lưu trữ.
Cơ chế này đảm bảo **phân tán dữ liệu, cân bằng tải, và khả năng chịu lỗi cao** trong toàn cụm Ceph.

<img src="images\theory\ceph-workflow.png">
**Quy trình cụ thể như sau:**

1. **Xác định đối tượng**: Mỗi đối tượng được xác định duy nhất bằng **tên đối tượng** và **ID của pool** (mỗi pool có một số ID). Ví dụ: Đối tượng "tree" trong pool "images" (ID = 7).
2. **Tính toán PG bằng hashing**:
    - Ceph lấy tên đối tượng (ví dụ: "tree") và tính giá trị **hash** (giả sử hash("tree") = 0xA062B8CF).
    - Giá trị hash này được lấy **modulo** với số lượng PG của pool (giả sử pool có 65,536 PG): 0xA062B8CF % 65,536 = 0xB8CF.
    - Kết hợp với ID của pool (7), Ceph tạo ra một PG duy nhất, ví dụ: **7.B8CF**.
3. **Ánh xạ PG tới OSD**:
    - Ceph sử dụng thuật toán **CRUSH** và **cluster map** (do MON cung cấp) để ánh xạ PG (7.B8CF) tới một danh sách OSD. Ví dụ: CRUSH(7.B8CF) = [OSD 4, OSD 19, OSD 3].
    - Danh sách này có số lượng OSD bằng số bản sao (replica) được cấu hình trong pool (ví dụ: 3 bản sao). OSD đầu tiên (OSD 4) là **primary OSD**, chịu trách nhiệm xử lý yêu cầu đọc/ghi chính. Các OSD tiếp theo (OSD 19, OSD 3) là **secondary OSD**, lưu bản sao dữ liệu để đảm bảo dự phòng.
4. **Client truy cập OSD**:
    - Client sử dụng cluster map từ MON để biết PG 7.B8CF ánh xạ tới [OSD 4, OSD 19, OSD 3].
    - Client giao tiếp trực tiếp với **primary OSD** (OSD 4) để đọc/ghi dữ liệu. Primary OSD đồng bộ dữ liệu với các secondary OSD để đảm bảo tính nhất quán.
5. **Đảm bảo tính sẵn sàng cao**:
    - Nếu primary OSD gặp sự cố, một secondary OSD (như OSD 19) sẽ được thăng cấp thành primary để tiếp tục phục vụ dữ liệu, đảm bảo hệ thống vẫn hoạt động.


**MON (Monitor)** không lưu trữ hoặc xử lý dữ liệu, mà chỉ quản lý **cluster map**, cung cấp thông tin ánh xạ PG-to-OSD cho client và các node lưu trữ. MON sử dụng giao thức Paxos để đạt đồng thuận trong các quyết định phân tán. Ceph ưu tiên **tính nhất quán** hơn **tính sẵn sàng**: cần ít nhất đa số MON (quorum) để cụm hoạt động. Ví dụ:

- Với 2 MON, nếu 1 MON thất bại (chỉ còn 50%), cụm sẽ ngừng hoạt động.
- Với 3 MON, nếu 1 MON thất bại, cụm vẫn hoạt động vì còn 2/3 MON.

## Kiến trúc đa lớp của Ceph 
Kiến trúc đa lớp của Ceph được thiết kế để tách biệt các dịch vụ người dùng khỏi cơ chế quản lý dữ liệu và lưu trữ vật lý, đảm bảo tính linh hoạt, mở rộng, và độ tin cậy. Kiến trúc này bao gồm ba tầng chính:

- **Lớp Dịch vụ Ceph**: Cung cấp giao diện lưu trữ (object, block, file) cho ứng dụng.
- **Lớp Lưu trữ (Ceph Storage Cluster)**: Quản lý dữ liệu phân tán dựa trên nền tảng RADOS.
- **Lớp phụ Storage Subsystem**: Lưu trữ dữ liệu thực tế trên phần cứng.

<img src="images\theory\ceph-multi-layer-structure.png">

### **1. Lớp dịch vụ Ceph** (Ceph Services)

Lớp này cung cấp các giao diện để ứng dụng và người dùng truy cập dữ liệu trong Ceph, dựa trên lõi RADOS. Các dịch vụ chính bao gồm:

- **RADOS Gateway (RGW)**: Cung cấp lưu trữ object, tương thích với API S3 và Swift, cho phép ứng dụng truy cập dữ liệu dưới dạng object, phù hợp cho cloud storage.
- **RADOS Block Device (RBD)**: Xử lý lưu trữ block, cung cấp ổ đĩa ảo cho máy ảo (VM) hoặc máy chủ vật lý, hỗ trợ các hệ điều hành sử dụng Ceph như thiết bị lưu trữ.
- **CephFS (Ceph File System)**: Cung cấp hệ thống tệp phân tán tuân thủ POSIX, hỗ trợ truy cập đồng thời từ nhiều máy khách, lý tưởng cho shared storage.

<aside>
❕

Lớp này cho phép Ceph tích hợp với các môi trường như OpenStack (RBD), Kubernetes (CephFS), hoặc lưu trữ object cho ứng dụng web (RGW).

</aside>

### **2. Lớp Lưu trữ (Ceph Storage Cluster)**

Lớp này là trung tâm của Ceph, dựa trên nền tảng **RADOS (Reliable Autonomic Distributed Object Store)**, chịu trách nhiệm lưu trữ và quản lý dữ liệu dưới dạng object trên cụm. RADOS đảm bảo tính mở rộng và chịu lỗi thông qua các daemon phân tán.

**Các tiến trình (daemons):** 

- **OSD (Object Storage Daemon)**: Lưu trữ dữ liệu thực tế trên các thiết bị (HDD, SSD, NVMe), mỗi OSD đại diện cho một thiết bị lưu trữ trong cụm.
- **MON (Monitor Daemon)**: Quản lý trạng thái cụm, bao gồm thông tin về node và OSD, yêu cầu ít nhất ba MON để đảm bảo tính sẵn sàng cao.
- **MDS (Metadata Server)**: Quản lý siêu dữ liệu cho CephFS, tăng tốc độ truy cập tệp trong hệ thống file.

<aside>
❕

Lớp này đảm bảo Ceph tự động hóa (self-healing, self-managing) và mở rộng khi thêm thiết bị hoặc node.

</aside>

### **3. Lớp phụ Storage Subsystem**

**Lớp này là tầng thấp nhất, chịu trách nhiệm lưu dữ liệu thực tế trên thiết bị vật lý. Nó trừu tượng hóa phần cứng để RADOS hoạt động linh hoạt trên các loại đĩa khác nhau (HDD, SSD, NVMe). Lớp này thường sử dụng BlueStore  làm hệ thống lưu trữ mặc định cho phép Ceph tận dụng phần cứng thông dụng (HDD, SSD, NVMe), hỗ trợ tiering (SSD cho hiệu suất, HDD cho dung lượng), cải thiện IOPS và giảm overhead so với FileStore (đã deprecated).**

## Data workflow đi qua các lớp

Dữ liệu từ các dịch vụ này được chuyển xuống lõi RADOS để quản lý và phân phối sau đó RADOS sử dụng thuật toán CRUSH để ánh xạ dữ liệu từ object tới các nhóm vị trí ( PGs) sau đó được phân phối tới các OSD (Object Storage Daemon) để lưu trữ  . Blue Store được sử dụng như hệ thống lưu trữ mặc định, đảm nhận việc quản lý và ghi dữ liệu xuống đĩa cứng một cách hiệu quả tại mỗi OSD.

> Ceph phân phối dữ liệu trên nhiều OSD để đạt được thông lượng cao hơn và tính sẵn sàng cao hơn.
> 

> BlueStore là một hệ thống lưu trữ hiệu quả, quản lý trực tiếp trên các ổ đĩa (HDD hoặc SSD) và khắc phục các hạn chế của các hệ thống lưu trữ cũ hơn
>