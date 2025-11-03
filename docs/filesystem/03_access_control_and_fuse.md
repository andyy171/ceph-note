# Filesystem in Userspace
- Filesystem in Userspace (FUSE) là một module lõi nạp được cho các hệ thống máy tính chạy hệ điều hành họ Unix, cho phép người dùng thông thường tạo hệ thống tệp mà không cần chỉnh sửa mã kernel. Điều này đạt được bằng cách chạy mã hệ thống tệp trong không gian người dùng, trong khi module FUSE chỉ cung cấp "cầu nối" đến giao diện kernel thực sự. FUSE đã chính thức tích hợp vào nhân Linux từ phiên bản 2.6.14.
- FUSE rất hữu ích cho việc viết các hệ thống tệp ảo. Không như các hệ thống tệp truyền thống đọc/ghi trực tiếp dữ liệu từ đĩa, hệ thống tệp ảo không lưu trữ dữ liệu. Phát hành dưới giấy phép GNU General Public License và GNU Lesser General Public License, FUSE là phần mềm tự do. FUSE có bản cho Linux, FreeBSD, NetBSD (như PUFFS), OpenSolaris, và Mac OS X.

# Các phương pháp truy xuất FS
Thông tin trong tập tin cần được truy xuất và đọc vào bộ nhớ để xử lý. Có nhiều cách truy xuất thông tin trong tập tin.
## Truy xuất tuần tự
Phương pháp đơn giản nhất, thông tin trong tập tin được xử lý theo thứ tự. Đây là chế độ thông dụng nhất, ví dụ: bộ soạn thảo và biên dịch.

## Truy xuất trực tiếp
Còn gọi là truy xuất tương đối. Tập tin hình thành từ các logical records có chiều dài không đổi, cho phép người lập trình đọc/ghi mẫu tin nhanh chóng, không theo thứ tự. Để truy xuất, tập tin được xem như chuỗi khối hoặc mẫu tin được đánh số. Phương pháp dùng cho truy xuất tức thời lượng lớn thông tin (như cơ sở dữ liệu).

## Các phương pháp truy xuất khác
Xây dựng trên cơ sở truy xuất trực tiếp, như xây dựng chỉ mục cho tập tin. Chỉ mục chứa con trỏ chỉ tới các khối khác. Để tìm mẫu tin: tìm chỉ mục, dùng con trỏ truy xuất trực tiếp và tìm mẫu tin mong muốn.

# Kiểm soát truy xuất
- Truy xuất dựa trên định danh người dùng. Cơ chế phổ biến là gắn với mỗi tập tin và thư mục một danh sách kiểm soát truy xuất (ACL) xác định tên người dùng và kiểu truy xuất phép cho mỗi người. Khi người dùng yêu cầu truy xuất tập tin cụ thể, hệ điều hành kiểm tra ACL gắn với tập tin. Nếu người dùng được liệt kê cho truy xuất yêu cầu, phép truy xuất; ngược lại, vi phạm bảo vệ xảy ra và từ chối truy xuất.
- Để tạo ACL, hệ thống phân loại người dùng theo mỗi tập tin:

+ Người sở hữu (Owner): người tạo tập tin.
+ Nhóm (Group): tập hợp người dùng chia sẻ tập tin và cần truy xuất tương tự.
+ Người dùng khác (universe): tất cả người dùng còn lại.

- Trên Unix, chỉ quản trị viên mới có quyền tạo và cài đặt danh sách.

# Thực thi File system
- Các cấu trúc và thao tác dùng để thực thi hệ thống tập tin. Một số on-disk và in-memory structures sử dụng để thực thi FS, phụ thuộc OS và FS, nhưng có nguyên tắc chung. Trên đĩa, FS chứa thông tin khởi động OS, tổng số khối, số và vị trí khối trống, cấu trúc thư mục, tập tin riêng biệt.
- Các cấu trúc trên đĩa:

+ Khối điều khiển khởi động (boot control block): chứa thông tin để khởi động OS từ volume. Nếu đĩa không chứa OS, khối này rỗng. Thường là khối đầu tiên. Trong UFS: boot block; NTFS: partition boot sector.
+ Khối điều khiển phân khu (partition control block): chứa chi tiết volume như số khối, kích thước khối, bộ đếm khối trống và con trỏ khối trống, bộ đếm FCB trống và con trỏ FCB. UFS: superblock; NTFS: Master File Table.
+ Directory structure: dùng tổ chức file. UFS: file name + inode liên kết; NTFS: lưu trong Master File Table.
+ Per-file FCB (file control block): chứa nhiều thông tin về file, có định danh riêng liên kết directory entry. NTFS: lưu trong Master File Table.

- In-memory information dùng quản lý FS và nâng cao hiệu năng qua caching, cập nhật trong hoạt động FS. Các loại:

+ In-memory mount table: thông tin mỗi mounted volume.
+ In-memory directory-structure cache: giữ directory thường truy cập.
+ System-wide open-file table: chứa bản sao FCB mỗi file mở, kèm thông tin bên cạnh.
+ Per-process open-file table: chứa con trỏ tới system-wide open-file table, kèm thông tin bên cạnh.
+ Buffers lưu file system block khi đọc/ghi từ/đến disk.


Để tạo file mới, app gọi logical file system. Nó nhận biết định dạng directory structures, cấp phát FCB mới, đọc thư mục tương ứng vào memory, cập nhật thư mục với file mới, ghi đĩa. FCB bao gồm:
<img src="/images/theory/filesystem/FCB.png" >

- Một số OS (Linux/Unix) đối xử directory như file, với trường phân biệt. Một số (Windows) phân biệt file và directory. Tùy kiến trúc, logical file system có thể gọi file-organization module để map directory I/O tới disk-block number, chuyển FS cơ bản, IO control system.

- Khi file tạo, để IO phải mở. Open() truyền filename tới logical file system – tìm system-wide open-file table kiểm tra file đang dùng bởi process khác. Nếu mở, per-process open-file table entry tạo con trỏ tới existing system-wide open-file table (tiết kiệm memory). Nếu không, tìm directory structure theo filename. Phần directory cached trong memory tăng tốc OS. Khi tìm, FCB sao chép tới system-wide open-file table trong memory. Table theo dõi số process dùng file. Entry tạo trong per-process open-file table, con trỏ tới system-wide, kèm trường khác (con trỏ vị trí hiện tại cho read/write, trạng thái truy cập). Open() trả con trỏ entry per-process file-system table. Tất cả hoạt động file qua con trỏ. Filename có thể không trong open-file table, system không dùng khi FCB định vị disk. Có thể cached tiết kiệm thời gian. Unix gọi file descriptor.

- Khi process đóng file, per-process table entry xóa. System-wide entry giảm. Khi tất cả user đóng, metadata update, copy tới disk-based directory structure, system-wide entry xóa.

- Caching FS structure quan trọng. Hầu hết sys giữ thông tin file mở trong memory, trừ data block.
<img src="/images/theory/filesystem/FS caching.png" >
