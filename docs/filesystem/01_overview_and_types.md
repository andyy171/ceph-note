# Tổng quan về File system
- File system (hệ thống quản lý tập tin) trong máy tính được sử dụng để kiểm soát việc lưu trữ và truy xuất dữ liệu. Nếu không có nó, thông tin lưu trữ trong các khối lớn sẽ không thể xác định được vị trí bắt đầu, kết thúc hay dữ liệu tiếp theo. Dữ liệu được chia thành các mảnh (files) và được đặt tên, giúp việc đánh dấu và xác thực thông tin trở nên dễ dàng. Khái niệm này có nguồn gốc từ hệ thống lưu trữ trên giấy, nơi các nhóm dữ liệu được gọi là "file".
- Có nhiều loại file system khác nhau, mỗi loại có cấu trúc, logic và tính chất riêng về tốc độ, bảo mật, kích thước, v.v. Ví dụ, ISO 9660 được thiết kế đặc biệt cho đĩa quang. File system được sử dụng trên nhiều loại thiết bị lưu trữ như ổ đĩa cứng, bộ nhớ flash, đĩa quang, và thậm chí là bộ nhớ chính (RAM) trong trường hợp của tmpfs (sử dụng làm bộ đệm tạm thời). Một số file system phục vụ việc truy cập file qua mạng (NFS, SMB), trong khi một số khác là ảo (virtual), cung cấp "file" ảo cho các yêu cầu tính toán.
- File system quản lý cả nội dung và metadata của file, chịu trách nhiệm tổ chức không gian lưu trữ một cách đáng tin cậy, rõ ràng và có hệ thống.

## Kiến trúc
File system thường bao gồm 2 hoặc 3 lớp, đôi khi được kết hợp:

1. Logical File System (Hệ thống tập tin logic):

- Tương tác với ứng dụng người dùng.
- Cung cấp API cho các hoạt động cơ bản (Mở, đóng, đọc, ghi).
- Quản lý các đối tượng đang mở như "file table" và "per-process file descriptors".
- Cung cấp các chức năng truy cập file, thao tác thư mục, bảo mật và bảo vệ.

2. Virtual File System (VFS - Hệ thống tập tin ảo) - Lớp không bắt buộc:
- Lớp giao diện cho phép hỗ trợ đồng thời nhiều loại file system vật lý (thực thi file system) khác nhau.

3. Physical File System (Hệ thống tập tin vật lý):
- Liên quan đến hoạt động vật lý của thiết bị lưu trữ (đĩa).
- Xử lý các khối vật lý (physical blocks) cho việc đọc/ghi.
- Quản lý buffer, bộ nhớ và chịu trách nhiệm bố trí các khối vật lý tại các vị trí được chỉ định.
- Tương tác với device drivers hoặc các kênh tới thiết bị lưu trữ.

### Các khía cạnh cốt lõi (Áp dụng với thiết bị lưu trữ)
- Tổ chức và Phân bổ: File system tổ chức file và thư mục, chỉ định các đơn vị phân vùng để lưu trữ.
+ Slack Space: Hiện tượng không gian lưu trữ dư thừa, không thể tận dụng được (xuất hiện khi kích thước file nhỏ hơn kích thước đơn vị cấp phát).
+ Phân mảnh (Fragmentation): Xảy ra khi không gian lưu trữ bị chia nhỏ hoặc các file đơn không còn nằm liền kề nhau do quá trình tạo, sửa, xóa file.

- Tên file (Filename): Được sử dụng để xác định vị trí lưu trữ. Hầu hết các file system đều có giới hạn về độ dài và quy tắc đặt tên.

- Thư mục (Directories): Cho phép nhóm các file riêng lẻ thành một tập hợp, thường được tổ chức dưới dạng phân cấp. Việc này có thể được thực hiện bằng cách gán file với số thứ tự trong table of content hoặc inode (trong hệ điều hành nhân Unix).

- Metadata: Thông tin đi kèm với mỗi file, bao gồm:
+ Độ dài dữ liệu (kích thước file, số block được phân bổ).
+ Thời gian chỉnh sửa/tạo cuối cùng.
+ Chủ sở hữu (UserID, Group ID), quyền truy cập.

## Nhiều File System trên cùng một hệ thống
Thông thường, một thiết bị lưu trữ được cấu hình với một file system duy nhất. Tuy nhiên, nhiều file system với thuộc tính khác nhau có thể được sử dụng đồng thời.

- **Ví dụ 1 (Bộ đệm)**: Bộ đệm của trình duyệt có thể được cấu hình để lưu trong các phân vùng cấp phát nhỏ, cho phép xóa/tạo mới liên tục mà không ảnh hưởng đến hệ thống lưu trữ chính.

- **Ví dụ 2 (Ảo hóa)**: Người dùng có thể chạy định dạng ext4 (Linux) trên máy ảo, trong khi máy ảo đó được lưu trữ trên một file system NTFS (Windows) của máy chủ. Ext4 được định dạng lại một disk image, và disk image này được lưu trên host NTFS.

### Các loại File System phổ biến
Disk File Systems (Hệ thống tập tin đĩa):
- Phổ biến: FAT (FAT12, FAT16, FAT32), exFAT, NTFS, HFS/HFS+, APFS, UFS, ext2, ext3, ext4, XFS, btrfs, ZFS, ISO 9660, UDF.
- Một số là journaling file systems (ghi nhật ký) hoặc versioning file systems (lưu phiên bản).

# Hệ thống Tập tin Ảo (Virtual File System - VFS) trong Linux
## VFS: Lớp Gián tiếp trong Nhân Linux
Nhân hệ điều hành Linux chứa lớp Virtual File System (VFS) để quản lý các lời gọi hệ thống liên quan đến tập tin.
- Vai trò: VFS hoạt động như một lớp gián tiếp (indirection layer). Nó xử lý các lời gọi hệ thống hướng tập tin (File-oriented System Calls), quản lý các thao tác độc lập cấu trúc, và chuyển hướng chúng đến các chức năng trong mã hệ thống tập tin vật lý (Physical File System) để thực hiện nhập/xuất (I/O).
- Lợi ích: Cơ chế này giúp Linux dễ dàng hòa nhập và sử dụng nhiều kiểu hệ thống tập tin khác nhau một cách đồng thời. *

## Cấu trúc Hệ thống Tập tin Ảo
VFS định nghĩa một bộ các chức năng chuẩn mà mọi hệ thống tập tin vật lý phải thực thi. Giao diện này được liên kết với ba kiểu đối tượng chính:

- Hệ thống tập tin (Filesystem):
- i-node:
- Tập tin mở (Open files):

## Quá trình Gắn vào (Mount)
- VFS duy trì một bảng các kiểu hệ thống tập tin được hỗ trợ (được định nghĩa khi cấu hình nhân).

- Khi một hệ thống tập tin được gắn vào, hàm mount tương ứng được gọi. Chức năng này sẽ đọc siêu khối (superblock) từ đĩa, khởi tạo các biến và trả về một bộ mô tả hệ thống tập tin đã gắn cho VFS.

<img src="/images/theory/filesystem/phancap.png">

- Bộ mô tả này chứa:
+ Dữ liệu thông tin chung.
+ Các con trỏ tới hàm (cung cấp bởi mã hệ thống tập tin vật lý) cho phép VFS truy cập hệ thống tập tin.
+ Dữ liệu riêng của hệ thống tập tin vật lý.

- Sau khi gắn vào, VFS sử dụng bộ mô tả này, cùng với bộ mô tả i-node và bộ mô tả tập tin mở, để truy cập hệ thống tập tin.

## Tổ chức Logic và Các Kiểu Tập tin Linux
Hệ thống tập tin Linux phân loại tập tin thành nhiều kiểu, mỗi kiểu có mục đích riêng:

| Kiểu Tập tin           | Mô tả |
|------------------------|-------|
| Regular                | Chỉ chứa dữ liệu (chương trình, văn bản, mã nguồn, v.v.). |
| Directory              | Chứa danh sách các tập tin và thư mục khác. Dữ liệu của nó chỉ là danh sách này. |
| Character Device       | Tham chiếu đến trình điều khiển thiết bị thực hiện I/O có bộ đệm (ví dụ: terminal). |
| Block Device           | Tham chiếu đến trình điều khiển thiết bị thực hiện I/O theo các đoạn lớn (512/1024 byte), yêu cầu nhân hệ điều hành thực hiện bộ đệm (ví dụ: đĩa cứng). |
| Domain Socket          | Cho phép giao tiếp nhanh chóng, tin cậy giữa các tiến trình, thường được sử dụng trong giao tiếp mạng. |
| Name Pipes             | Cho phép truyền thông giữa hai tiến trình không có quan hệ trên cùng một máy. |
| Hard Link              | Không phải là kiểu tập tin riêng biệt, mà là một liên kết (alias/tên hiệu) trực tiếp đến cùng một tập tin. Thay đổi nội dung của hard link sẽ thay đổi nội dung của tập tin gốc và ngược lại. |
| Symbolic Link (Symlink)| Một tập tin chỉ chứa tên của tập tin khác. Khi truy cập, nhân được dẫn đến tập tin mà symlink chỉ đến (tham chiếu bởi tên). |

# Các Loại File System Phổ Biến trong Linux
## Dòng Ext (Extended File System)
- Dòng Ext là định dạng FS đầu tiên được thiết kế riêng cho Linux, với tổng cộng 4 phiên bản, mỗi phiên bản là một sự nâng cấp đáng kể.

| Phiên bản FS | Đặc điểm nổi bật | Ưu điểm & ứng dụng | Hạn chế |
|--------------|------------------|---------------------|---------|
| **Ext** | Phiên bản đầu tiên, nâng cấp từ Minix. | Xử lý file hệ thống tới 2 GB. | Nhiều hạn chế, không còn được hỗ trợ rộng rãi. |
| **Ext2** | Phiên bản thương mại đầu tiên, **không phải là journaling FS**. | Mạnh mẽ, hỗ trợ ổ cứng tới 2 TB, tên file dài (tối đa 255 ký tự). Thích hợp cho thiết bị có I/O thấp (USB, SD Card). | Không có tính năng Journaling (dễ mất dữ liệu khi lỗi hệ thống). |
| **Ext3** | **Ext2 có thêm Journaling.** | Tương thích ngược với Ext2 (chuyển đổi dễ dàng). Hoạt động nhanh và ổn định hơn Ext2. | Giới hạn của Ext2 vẫn còn. **Không hỗ trợ Disk Snapshot.** Không phù hợp làm FS cho máy chủ. |
| **Ext4** | Kế thừa Ext3, giữ **tính tương thích ngược cao.** | Giảm phân mảnh, hỗ trợ file và phân vùng dung lượng lớn. Tăng hiệu suất, phù hợp với **SSD**. Phù hợp cho Server hơn Ext3. | Hiệu suất trên Server vẫn chưa bằng các FS thế hệ mới (như BtrFS). |

>Lưu ý: Journaling (Ghi nhật ký) giúp phục hồi nhanh chóng và tránh mất dữ liệu sau khi hệ thống gặp sự cố.
>
## Các File System Thế Hệ Mới và Chuyên Dụng
| Tên FS | Phát triển bởi | Tính năng cốt lõi | Ưu điểm & Ứng dụng | Hạn chế |
|--------|----------------|-------------------|---------------------|---------|
| **BtrFS** | Oracle | **B-Tree FS.** Hỗ trợ Pool, Snapshot (lưu trữ nhanh), Nén dữ liệu, chống phân mảnh nhanh. | Hiệu suất cao, rất phù hợp với Server. Thay thế tiềm năng cho Ext4. Chuyển đổi nhanh chóng từ Ext3/4. | Vẫn đang trong giai đoạn phát triển, không ổn định trên một số distro. Hiệu suất kém hơn Ext4 với SSD/Server Database. |
| **ReiserFS** | | Một trong những bước tiến lớn về FS Linux. | Hiệu suất rất cao với file nhỏ (file log). Phù hợp với Server email và Database. | Quá trình phát triển Reiser4 chậm và chưa hỗ trợ đầy đủ kernel Linux. |
| **XFS** | Silicon Graphics | Journaling FS. Hạn chế phân mảnh, hỗ trợ file dung lượng lớn, có thể thay đổi kích thước (resize) phân vùng. | Rất phù hợp với Server Media (truyền tải video tốt). | Không thể Shrink (chia nhỏ) phân vùng. Hiệu suất kém với file dung lượng nhỏ (không phù hợp Database/Email/Log Server). |
| **JFS** | IBM | Journaling FS. | Tiêu tốn ít tài nguyên hệ thống nhất. Tốc độ kiểm tra ổ đĩa nhanh nhất so với Ext. | Có thể tăng kích thước (resize) nhưng không thể Shrink. |
| **ZFS** | Oracle/Sun CDDL | Tương tự BtrFS (Pool, Snapshot, Copy-on-Write). | Độ tin cậy và quản lý dữ liệu cao. | Không tương thích trực tiếp với nhân kernel Linux (do vấn đề cấp phép CDDL/GPL). Cần sử dụng qua FUSE (Filesystem in Userspace) để hoạt động. |

## Khái niệm Đặc biệt: SWAP
Swap không phải là một File System theo nghĩa truyền thống.

- Cơ chế: Hoạt động như một bộ nhớ ảo (virtual memory), không có cấu trúc file system cụ thể.

- Mục đích: Chỉ được sử dụng bởi kernel để ghi dữ liệu vào ổ cứng khi:
+ Hệ thống thiếu hụt bộ nhớ RAM.
+ Chuyển trạng thái máy tính sang chế độ Hibernate (ngủ đông).

- Đặc điểm: Dữ liệu trong phân vùng Swap không thể được đọc trực tiếp hay kết hợp như các file system thông thường.