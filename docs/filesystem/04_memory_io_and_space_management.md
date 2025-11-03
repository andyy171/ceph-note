# Cấp Phát Không Gian Ổ Đĩa (Disk Space Allocation)
Đây là các phương pháp tối ưu hóa việc lưu trữ các khối dữ liệu của tệp trên đĩa nhằm tăng tốc truy vấn.

## 1. Cấp Phát Kề (Contiguous Allocation)
- **Cơ chế:** Cấp phát cho tệp một tập hợp các khối liên tiếp trên đĩa. Địa chỉ được xác định theo thứ tự tuyến tính (từ *b* đến *b+n-1*).
- **Ví dụ Tối ưu:** Khi truy vấn, đầu đọc di chuyển tuần tự qua các sector và cylinder, tối ưu hóa thời gian tìm kiếm.
- **Vấn đề:**
+ **Tìm không gian mới:** Sử dụng các thuật toán như First Fit hoặc Best Fit.
+ **Mở rộng tệp:** Khó khăn khi tệp cần thêm không gian mà không có khối kề trống. Giải pháp là dùng đoạn mở rộng (extent).
+ **Phân mảnh ngoài**(External Fragmentation) ổ đĩa.
<img src="/images/theory/filesystem/cp-1.png">

## 2. Cấp Phát Liên kết (Linked Allocation)
- **Cơ chế:** Tệp được lưu dưới dạng một danh sách liên kết các khối (block) phân tán trên đĩa. Mỗi khối lưu một con trỏ đến khối tiếp theo.
- **Không gian con trỏ:** Ví dụ: Block 512 byte -> 4 byte con trỏ, lưu 508 byte data.
- **Ưu điểm:**
+ **Không phân mảnh** ổ đĩa.
+ Kích thước tệp không cần xác định trước (rất linh hoạt).
- **Nhược điểm:**
+ **Chỉ phù hợp truy xuất tuần tự**, không thể truy xuất trực tiếp (ngẫu nhiên).
+**Tốn không gian** cho con trỏ (trung bình bất 0.77% disk).
+ **Mất con trỏ** có thể dẫn đến mất dữ liệu phía sau (giải pháp: danh sách liên kết đôi).
<img src="/images/theory/filesystem/cp-2.png">

## 3. Cấp Phát được Lập Chỉ Mục (Indexed Allocation)

- **Cơ chế:** Mang tất cả con trỏ của tệp về một vị trí duy nhất: 
+ Khối Chỉ Mục (Index Block). Khối chỉ mục là một mảng các địa chỉ khối. Tương tự cơ chế phân trang.
- **Hoạt động:** Khi tạo file, các con trỏ trong Khối Chỉ Mục bằng null. Khi ghi block mới, địa chỉ được đưa vào index block theo thứ tự.
- **Ưu điểm:**
+ Hỗ trợ truy xuất trực tiếp/ngẫu nhiên nhanh chóng.
+ Tránh được phân mảnh.
+ Khối Chỉ Mục có thể được cache để tăng tốc tìm kiếm.

- **Vấn đề:**Tiêu tốn không gian lưu chỉ mục.
<img src="/images/theory/filesystem/cp-3.png">

## Một số Phương pháp Mở rộng
- **Cơ chế Liên kết (Linked Scheme):** Dùng để lưu trữ các tệp lớn, liên kết nhiều Khối Chỉ Mục lại với nhau.
- **Chỉ mục Nhiều Cấp (Multilevel Index):** Phân cấp khối chỉ mục (Khối cấp 1 chỉ khối cấp 2, khối cấp 2 chỉ khối dữ liệu). Giúp quản lý tệp cực lớn.
- **Cơ chế Kết hợp (Combined Scheme):** Sử dụng trong UFS/Linux. Quản lý 15 con trỏ đầu tiên (một số trực tiếp, một số chỉ mục đơn/đôi/ba) ngay trong cấu trúc inode của tệp.
<img src="/images/theory/filesystem/cp-4.png">

# Quản Lý Không Gian Trống (Free Space Management)
OS cần biết không gian trống để cấp phát cho tệp mới.

| Phương pháp | Mô tả | Ưu điểm | Nhược điểm/Vấn đề |
|-------------|-------|---------|------------------|
| **Bit Vector (Bit Map)** | Mỗi block được đại diện bởi 1 bit. 1 = Trống, 0 = Cấp phát. | Đơn giản, nhanh tìm khối trống hoặc một dãy khối trống. | Tốn không gian bộ nhớ để lưu trữ toàn bộ vector/map. |
| **Danh sách Liên kết** | Các khối trống được liên kết với nhau bằng con trỏ. Chỉ cần lưu con trỏ đầu tiên. | Không gây phân mảnh, không tổn thêm không gian ngoài các khối trống. | Bắt buộc truy xuất tuần tự, tổn thời gian khi tìm kiếm. |
<img src="/images/theory/filesystem/kg-1.png">

# Hệ Thống I/O (I/O Systems)
Vai trò quan trọng của OS là quản lý hoạt động I/O (Input/Output): điều khiển thiết bị, quản lý nhập/xuất.

## Khái Niệm Cơ Bản & I/O Hardware
- **Quản lý I/O**: Tạo I/O subsystem trong Kernel, tách biệt Kernel khỏi sự phức tạp của các thiết bị.

- **Device Drivers**: Cung cấp phương thức cho OS giao tiếp với thiết bị (tăng linh hoạt).

- **Cổng (Port) & Bus**: Điểm kết nối (Port), tập hợp dây/giao thức truyền tín hiệu (Bus - PCI, Expansion, SCSI, PCIe).

- **Bộ Điều khiển (Controller)**: Tập linh kiện trên port/bus/device, chứa các thanh ghi (Status, Control, Data-in, Data-out) để CPU đọc/ghi.
<img src="/images/theory/filesystem/io-sys-1.png">

- **Memory-Mapped I/O**: Thanh ghi của Controller được ánh xạ vào không gian địa chỉ vật lý, cho phép CPU dùng lệnh truyền dữ liệu thông thường để thao tác.


## Cơ chế Tương tác Host - Controller
| Cơ chế | Mô tả | Vai trò |
|--------|-------|---------|
| **Polling (Thăm dò)** | Host (CPU) lặp đi lặp lại để đọc Busy bit và Status Register của Controller cho đến khi lệnh hoàn thành. | Giao thức "bắt tay" đơn giản nhất, đảm bảo đồng bộ giữa Host và Controller. |
| **Ngắt (Interrupt)** | Controller gửi một tín hiệu Interrupt-Request Line đến CPU khi I/O hoàn tất hoặc có sự kiện cần xử lý. | Giảm lãng phí CPU (tránh Polling). CPU lưu trạng thái, nhảy đến Interrupt Handler, xử lý và trở về. |
| **DMA (Direct Memory Access)** | Controller chuyên dụng (DMA Controller) thực hiện truyền dữ liệu trực tiếp giữa thiết bị và bộ nhớ mà không cần qua CPU. | Giảm gánh nặng CPU khi truyền dữ liệu lớn (ví dụ: từ đĩa). Chỉ cần CPU khởi tạo khối lệnh. |

## Tối ưu hóa Dữ liệu
| Khái niệm | Chức năng | Khác biệt chính |
|-----------|-----------|-----------------|
| **Vùng Đệm (Buffer)** | Vùng nhớ tạm thời để lưu trữ data khi chuyển giao. | Giải quyết sự không tương thích về tốc độ và kích thước truyền giữa các thành phần. |
| **Vùng Lưu trữ Đệm (Cache)** | Vùng nhớ nhanh quản lý bản sao data. | Giữ bản sao nhanh, giúp truy xuất hiệu quả hơn so với truy xuất bản gốc chậm hơn. |