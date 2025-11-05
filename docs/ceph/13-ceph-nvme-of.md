# Khái nieenmj cốt lõi 

## NVMe-oF là gì?
- Là một giao thức mạng cho phép truy cập các thiết bị lưu trữ NVMe từ xa.
- Sử dụng các kết nối mạng tốc độ cao (như InfiniBand, RoCE) thay vì bus PCIe thông thường.
- Giúp thu hẹp đáng kể khoảng cách về hiệu suất giữa lưu trữ cục bộ và lưu trữ từ xa, giảm độ trễ xuống chỉ còn vài micro giây. 

## Các thuật ngữ NVMe và Ánh xạ với Ceph (Terminology)
Khi làm việc với Ceph NVMe-oF Gateway, việc hiểu rõ các thuật ngữ của giao thức NVMe và cách chúng ánh xạ tới các thực thể Ceph là rất quan trọng:
- **Namespace:** Đây là đơn vị lưu trữ cơ bản nhất trong NVMe, tương đương với một **iSCSI/FC LUN**. Trong kiến trúc Ceph NVMe-oF Gateway, một Namespace được ánh xạ trực tiếp tới một RBD Image trong Ceph Cluster.
- **Subsystem:** Đây là thực thể chính mà **Initiator (Host)** kết nối tới, sử dụng địa chỉ IP và Port. Subsystem là một Container logic chứa nhiều Namespace và được nhận dạng bằng một tên duy nhất gọi là **NQN (NVMe Qualified Name)**. Nó đóng vai trò quan trọng trong việc định nghĩa các chính sách kiểm soát truy cập (Access Control) cấp cao.
- **IO Controller:** Đây là một phiên làm việc (session) được tạo ra trên Target (Gateway) cho mỗi kết nối của Host tới một Subsystem. **IO Controller** chịu trách nhiệm xử lý các luồng I/O (Read/Write) cho Namespace. Nếu cùng một Host kết nối tới nhiều Subsystem, sẽ có nhiều IO Controller được tạo ra.
- **Initiator (Host):** Là máy chủ khách gửi yêu cầu I/O và khởi tạo kết nối tới Subsystem.
- **Gateway (Target):** Là điểm cuối (Endpoint) chạy giao thức NVMe/TCP. Đây là nơi triển khai SPDK để xử lý I/O Path.

<img src="/images/theory/nvme-terminology.png">

## Kiến trúc và cấu tạo của Ceph NVME-oF Gateway
Kiến trúc của **Ceph NVMe/TCP Gateway**

<img src="/images/theory/ceph-nvme-tcp-gateway.png">


<img src="/images/theory/ceph-nvme-of-gateway.png">


Kiến trúc của **Ceph NVMe-oF Gateway** được thiết kế để tách biệt rõ ràng giữa quản lý và I/O, đồng thời hỗ trợ mở rộng.

- Các Thành phần Chính của Gateway:

+ **Control Plane:** Thành phần này chịu trách nhiệm quản lý và cấu hình Gateway, bao gồm việc đọc và lưu trữ cấu hình. Nó cung cấp Management API thông qua gRPC và hỗ trợ bảo mật bằng mTLS để đảm bảo giao tiếp quản lý an toàn.

+ **I/O Path:** Phần này được triển khai bằng SPDK (Storage Performance Development Kit). Control Plane sẽ cấu hình SPDK, sau đó SPDK đảm nhiệm việc xử lý luồng I/O hiệu năng cao.

+ **Cấu hình:** Cấu hình của Gateway (bao gồm thông tin Subsystem và Namespace) được lưu trữ trong một đối tượng Ceph OMAP, đảm bảo rằng tất cả các Gateway trong cùng một nhóm đều đọc và chia sẻ cùng một trạng thái cấu hình.

- Hỗ trợ Đa Gateway (Multiple Gateways):

+ **Kiến trúc hỗ trợ triển khai nhiều Gateway** trên cùng một Ceph Cluster. Mục đích kép là để Phân tán Tải (Load Distribution) I/O NVMe/TCP trên nhiều Node Ceph và đạt được Tính Sẵn sàng Cao (HA).

+ **Gateway Group:** Là một tập hợp các Gateway được cấu hình để chia sẻ cùng một tập hợp Subsystem và Namespace, phục vụ cho một nhóm Initiator nhất định. Việc này cũng cho phép phân chia tài nguyên và cô lập người dùng (Multi-tenancy).


# HIGH AVAILABILITY (HA) VÀ FAILOVER
Các cơ chế kỹ thuật giúp Ceph NVMe-oF Gateway đạt được tính sẵn sàng cao, khả năng chịu lỗi, và phục hồi nhanh khi sự cố.

## Kiến trúc Tổng thể HA Group

- NVMe-oF Gateway được triển khai theo mô hình nhóm, gọi là HA Group (High Availability Group). Đây là đơn vị cơ bản đảm bảo tính sẵn sàng cao cho dịch vụ NVMe-oF.
- Mỗi HA Group phải có ít nhất 2 Gateway để đảm bảo khả năng dự phòng. Nếu chỉ có một Gateway duy nhất, hệ thống sẽ không đạt trạng thái HA thực sự.
<img src="/images/theory/ceph-gw-group.png">

- Tất cả các Gateway trong cùng một HA Group **chia sẻ cùng một cấu hình Ceph cluster**. Các thông tin về Subsystem, Namespace mapping, ANA Group, QoS, Access Control, và các khóa bảo mật đều được **đồng bộ thông qua Ceph Manager (MGR) module** `nvmeof`.

=> **Lợi ích:**

- Giảm downtime khi một Gateway lỗi.

- Tự động cân bằng tải (Load Balancing) giữa các Gateway.

- Cấu hình được quản lý tập trung, tránh sai lệch cấu hình giữa các node.

## Cơ chế Hoạt động của HA
Tính sẵn sàng cao được đảm bảo thông qua sự phối hợp của ba thành phần chính: Discovery, Multipath, và NVMe ANA (Asymmetric Namespace Access).

- **Discovery và Multipath**
<img src="/images/theory/nvme-of-discovery.png">

+ Khi Host gửi lệnh Discovery tới bất kỳ Gateway nào trong nhóm, Gateway đó sẽ trả về danh sách đầy đủ IP của tất cả Gateway trong HA Group.

+ Host sau đó thực hiện kết nối NVMe Connect tới toàn bộ các Gateway này, tạo ra các đường dẫn I/O song song (multipath).
Việc thiết lập multipath là bắt buộc để đạt được khả năng Failover tự động.
<img src="/images/theory/nvme-of-discovery-2.png">


+ **Yêu cầu:**
Host phải bật tính năng multipath:
```
nvme multipath enable
```
và sử dụng trình điều khiển NVMe native có hỗ trợ ANA.

- **Quản lý Đường dẫn I/O với NVMe ANA:**

+ Hệ thống sử dụng giao thức NVMe ANA (Asymmetric Namespace Access), tương tự như cơ chế ALUA trong SCSI.
ANA cho phép Gateway thông báo cho Host biết đường dẫn nào đang Optimized (Active) và đường dẫn nào đang Non-optimized (Standby).
<img src="/images/theory/nvme-of-discovery-3.png">

- Phân chia trách nhiệm:

+ Mỗi Gateway trong nhóm chịu trách nhiệm cho một tập hợp Namespace nhất định, gọi là ANA Group.

+ ANA Group là tập hợp các Namespace mà Gateway đó là Owner (chủ sở hữu chính).

+ I/O tới Namespace đó sẽ được định tuyến qua đường dẫn Optimized của Gateway Owner.

- Cân bằng tải:

+ Các Namespace (RBD Image) được chia đều giữa các Gateway trong nhóm.

+ Khi có nhiều Gateway hoạt động, hệ thống đạt trạng thái Active-Active (mỗi Gateway chủ sở hữu một phần workload).

- **Cơ chế Failover:**

+ Khi một Gateway gặp sự cố hoặc ngừng phản hồi:

* Ceph NVMe Monitor sẽ phát hiện mất tín hiệu (beacon timeout).

* ANA Group của Gateway đó sẽ được chuyển giao (Take Over) sang một Gateway khác trong cùng nhóm.

+ Gateway mới nhận quyền sở hữu sẽ:

* Đánh dấu các đường dẫn I/O qua nó là Optimized.

* Thông báo trạng thái cập nhật cho các Host thông qua ANA transition event.

+ Quá trình Failover diễn ra trong suốt, không yêu cầu Host reconnect thủ công.
Các I/O đang hoạt động sẽ được tự động chuyển hướng sang đường dẫn mới.

+ Cơ chế Block Listing được sử dụng để ngăn chặn tình trạng I/O đồng thời từ nhiều đường dẫn khác nhau, đảm bảo tính toàn vẹn dữ liệu.

## Failback (Phục hồi Chủ sở hữu)
- Khi Gateway bị lỗi phục hồi hoạt động và gửi lại tín hiệu Beacon:

+ NVMe Monitor sẽ kích hoạt quy trình Failback, trả lại quyền sở hữu ANA Group ban đầu.

+ ANA state trên Host sẽ tự động cập nhật lại để đưa đường dẫn về trạng thái Optimized.

- Việc này giúp khôi phục trạng thái cân bằng tải ban đầu giữa các Gateway.

## Giám sát và Phát hiện Lỗi (NVMe Monitor)

Việc giám sát liên tục là yếu tố then chốt để kích hoạt quá trình Failover.

<img src="/images/theory/nvme-monitor.png">

- **Dịch vụ NVMe Monitor:** Đây là một dịch vụ giám sát mới được triển khai như một phần của Ceph Monitor (MON) đóng vai trò trung tâm giám sát trạng thái hoạt động của các Gateway trong từng HA Group.

- **Hoạt động:** Mỗi Gateway định kỳ gửi Beacon (heartbeat signal) tới NVMe Monitor để báo cáo trạng thái hoạt động. Các thông tin được gửi bao gồm: **ID của Gateway, trạng thái hoạt động, danh sách ANA Group mà nó sở hữu, và thông tin cấu hình đồng bộ.**

- **Phát hiện lỗi và Kích hoạt Failover:** 
+ Nếu NVMe Monitor không nhận được Beacon liên tiếp trong nhiều chu kỳ (ví dụ 3 chu kỳ 5s), nó sẽ:

* Đánh dấu Gateway đó là Dead.

* Kích hoạt quy trình Failover để chuyển ANA Group của Gateway đó sang các Gateway còn lại trong nhóm.

>Thời gian phát hiện lỗi và failover có thể điều chỉnh thông qua tham số cấu hình trong Ceph MGR.

- **Đồng bộ Cấu hình:** Các Gateway trong cùng một HA Group chia sẻ cùng database cấu hình thông qua Ceph cluster.
Khi cấu hình được thay đổi trên một Gateway (ví dụ tạo Subsystem hoặc thêm Namespace), thay đổi đó sẽ được cập nhật tự động tới toàn bộ nhóm


# TÍNH NĂNG QUẢN LÝ VÀ BẢO MẬT (MANAGEMENT & SECURITY)

Các tính năng giúp vận hành Ceph NVMe-oF dễ dàng, an toàn và tuân thủ các quy tắc QoS

## Quản lý Chất lượng Dịch vụ (QoS)
Khả năng kiểm soát I/O là quan trọng để cô lập và bảo vệ các ứng dụng khác nhau.

- Đặc điểm QoS: Chức năng QoS được xây dựng trên nền tảng của SPDK và được cấu hình thông qua API của Gateway.

- Áp dụng: QoS được áp dụng ở cấp độ Namespace và từng Gateway riêng lẻ (hiện chưa hỗ trợ QoS phân tán trên nhiều Gateway).

- Giới hạn: Có thể thiết lập các giới hạn cứng (Maximum Limit) cho các thông số:

+ Tổng IOPS (Max IOPS).

+ Tổng Băng thông (Max Bandwidth).

+ IOPS ghi tối đa (Max Write IOPS).

## Kiểm soát Truy cập (Access Control)
Cơ chế phân quyền được thực hiện theo lớp để đảm bảo an ninh mạng.

- Subsystem Masking:

+ Đây là lớp kiểm soát truy cập mặc định của giao thức NVMe.

+ Nó cho phép định nghĩa danh sách các Host NQN được phép kết nối tới một Subsystem. Host nào không nằm trong danh sách sẽ bị từ chối kết nối.

- Namespace Masking (Đang phát triển):

+ Cung cấp lớp kiểm soát truy cập chi tiết hơn (Fine-Grained).

+ Cho phép chỉ định danh sách các Host NQN được phép truy cập vào từng Namespace riêng lẻ trong Subsystem. Điều này cần thiết để chia sẻ Subsystem nhưng hạn chế quyền truy cập vào các LUN cụ thể.

## Xác thực và Mã hóa
Bảo mật được phân loại thành bảo mật lưu lượng I/O và bảo mật giao tiếp quản lý.

- **Xác thực Inbound (CHAP):**

+ Sử dụng giao thức **CHAP (Challenge-Handshake Authentication Protocol)** để xác thực Host (Initiator) khi kết nối.

+ Lưu ý: CHAP CHỈ là cơ chế xác thực (Authentication), không phải kiểm soát truy cập (Access Control). Nó chỉ đảm bảo Host là chính chủ, không giới hạn quyền truy cập của Host đó sau khi kết nối.

+ Có thể cấu hình **Uni-directional** (chỉ Host xác thực) hoặc Bi-directional (cả Host và Target xác thực lẫn nhau).

- **Mã hóa In Transit (TLS):**

+ Mã hóa lưu lượng I/O giữa Host và Gateway. Hỗ trợ chế độ PKS (Pre-Shared Keys).

+ **Hạn chế:** Hiện tại, hầu hết các trình khởi tạo (Initiator) của Linux và ESXi Downstream vẫn chưa hỗ trợ TLS cho NVMe-oF I/O.

- **mTLS (Management Plane):**

+ Sử dụng **Mutual TLS** để bảo mật kênh giao tiếp gRPC (Control Plane) giữa CLI/API và Gateway. Cấu hình này được quản lý thông qua Ceph ADM và đảm bảo các lệnh quản lý không bị nghe lén.

# HIỆU SUẤT VÀ KHẢ NĂNG MỞ RỘNG (PERFORMANCE & SCALING)
Các vấn đề về tài nguyên, giới hạn mở rộng và chiến lược tối ưu hiệu suất của Ceph NVMe-oF.

## Thách thức về Tài nguyên và I/O

Việc sử dụng **SPDK (Storage Performance Development Kit)** mang lại hiệu suất cao nhưng cũng đặt ra yêu cầu cao về tài nguyên.

- **Vấn đề Safe Context:**

+ Mỗi Bev (Namespace) trong SPDK cần cấp phát các Safe Context (các luồng và tài nguyên Ceph).

+ Mỗi Safe Context yêu cầu nhiều tài nguyên (vài luồng, hàng chục MB RAM). Nếu cấp phát 1:1, hệ thống sẽ nhanh chóng cạn kiệt CPU và RAM (hàng chục nghìn luồng, hàng chục GB RAM).

+ **Giải pháp Default:** Ceph sử dụng cơ chế cấp phát 1 Safe Context cho một nhóm Namespaces (ví dụ: 1 Safe Context cho 32 Namespace hoặc 42 VMs) để cân bằng giữa hiệu suất và tài nguyên. Cấu hình này có thể điều chỉnh được.

- **Sử dụng CPU:**

+ SPDK sử dụng mô hình **Polling (thăm dò)** trên các **Reactor Cores** (mỗi Reactor chiếm 1 Core) để đạt độ trễ thấp. Do đó, các Reactor Cores thường chạy ở mức **100% CPU**. Cần phân bổ Core CPU riêng biệt cho Reactor.

- **Tối ưu hóa Bộ nhớ:** SPDK yêu cầu sử dụng Huge Pages (Bộ nhớ Lớn) để đạt hiệu suất cao nhất. Việc không sử dụng Huge Pages sẽ ảnh hưởng lớn đến độ trễ và thông lượng.

## Khả năng Mở rộng (Scale Limits)

Các giới hạn được đặt ra dựa trên việc sử dụng tài nguyên CPU/RAM để đảm bảo độ ổn định.

- **Giới hạn Hiện tại (Tentacle/Phiên bản mới):**

+ **Gateways/Group:** Tối đa 8.

+ **Subsystem/Cluster:** Tối đa 128.

+ **Namespace (trong nhóm):** Tối đa 1024.

+ **Host/Subsystem:** Tối đa 128.

- **Mở rộng Cluster:** Việc tăng số lượng OSD trong cụm sẽ cải thiện độ ổn định và thông lượng của NVMe-oF Gateway, đặc biệt là giảm thiểu độ trễ.

## Các Hướng Phát triển Hiệu suất trong Tương lai
Các nỗ lực tập trung vào việc giảm thiểu chi phí xử lý và tối ưu hóa đường dẫn dữ liệu.

- **Giảm Tài nguyên:**

+ Thay đổi thuật toán phân bổ Safe Context để tối ưu hóa việc sử dụng luồng và bộ nhớ.

+ Giảm số lượng luồng và bộ nhớ tiêu thụ cho mỗi Safe Context.

- **Mô hình Reactor:** Chuyển sang mô hình Reactor cho libRBD và librados để phù hợp với kiến trúc SPDK, giúp giảm chi phí copy dữ liệu và cải thiện khả năng mở rộng.

- **Tối ưu Hóa Messenger (Backend):**

+ Cải thiện Messenger (giao tiếp nội bộ giữa các daemon) để giảm thiểu thao tác **Data Copy** và tận dụng khả năng Zero-Copy Network (chuyển dữ liệu trực tiếp giữa bộ nhớ đệm ứng dụng và phần cứng mạng).

- **Offload Hardware:** Tận dụng bộ tăng tốc phần cứng (Hardware Accelerators) như:

+ **Intel DSA (Data Stream Accelerator):** Offload các tính toán nặng như CRC (kiểm tra tính toàn vẹn) và mã hóa/giải mã.

+ **TLS Offload:** Chuyển các tác vụ TLS (nếu được áp dụng cho Messenger) sang Card Mạng (NIC).