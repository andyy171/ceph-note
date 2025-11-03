# Cấu Trúc Vật lý của File System (Linux)
- Cấu trúc File System được tổ chức dựa trên đơn vị cơ bản là khối (block), có kích thước cố định phụ thuộc vào kích thước của toàn bộ hệ thống tập tin. Toàn bộ FS được chia thành các nhóm khối (block group).

## Thành phần của Nhóm Khối (Block Group)
Mỗi nhóm khối chứa các cấu trúc dữ liệu mô tả trạng thái và vị trí của dữ liệu trong nhóm đó:
- **Superblock**: Chứa các thông tin cơ bản và quan trọng nhất về toàn bộ FS (tổng số i-node, tổng số khối, trạng thái FS, v.v.).
- **Group Descriptors**: Một mảng các cấu trúc mô tả từng nhóm khối (vị trí bảng i-node, bản đồ khối, v.v.).*
- **Block Bitmap**:
+ Thường đặt ở khối đầu tiên của nhóm.
+ Mỗi bit đại diện cho trạng thái sử dụng của một khối dữ liệu trong nhóm đó ($1 = đang dùng, 0 = chưa dùng$).
- **i-node Bitmap**:Tương tự Block Bitmap, mỗi bit đại diện cho trạng thái sử dụng của một i-node trong bảng i-node.
- **i-node Table (Bảng i-node)**: Lưu trữ tất cả các i-node (mỗi i-node chứa thông tin mô tả một tập tin vật lý).
- **Data Blocks (Khối Dữ liệu)**: Lưu trữ nội dung thực tế của các tập tin, danh sách thư mục, symbolic link, v.v.
<img src="/images/theory/filesystem/filesystem-structure.png">

## i-node: Mô tả Tập tin
Mỗi tập tin trên hệ thống được đại diện bởi một cấu trúc kích thước cố định duy nhất gọi là i-node (index-node).

- Vai trò: Lưu trữ tất cả metadata về một tập tin vật lý, bao gồm:
+ Số i-node (chỉ số duy nhất trong Bảng i-node).
+ Chủ sở hữu, quyền truy cập (permissions).
+ Kích thước tập tin.
+ Thời gian thay đổi nội dung, thời gian truy cập sau cùng.
+ Số lượng hard link trỏ tới tập tin.
+ Các con trỏ địa chỉ tới các khối dữ liệu (Data Blocks) chứa nội dung thực của tập tin.
### Cơ chế Con trỏ Địa chỉ trong i-node
i-node sử dụng một hệ thống con trỏ đa cấp để ánh xạ các khối dữ liệu, cho phép quản lý các tập tin có kích thước rất lớn:

1. **Con trỏ trực tiếp (Direct Pointers)**: Khoảng 10 con trỏ đầu tiên trỏ trực tiếp đến các khối dữ liệu. Đây là cách truy cập nhanh nhất cho các tập tin nhỏ.

2. **Con trỏ Gián tiếp Đơn (Single Indirect Block)**: Con trỏ tiếp theo trỏ đến một khối trên đĩa (Single Indirect Block). Khối này lại chứa danh sách các địa chỉ trỏ đến các khối dữ liệu thực.

3. **Con trỏ Gián tiếp Đôi (Double Indirect Block)**: Con trỏ thứ 12 trỏ đến một khối trên đĩa (Double Indirect Block). Khối này chứa danh sách các địa chỉ của các Single Indirect Block.

4. **Con trỏ Gián tiếp Ba (Triple Indirect Block)**: Nếu vẫn chưa đủ, một con trỏ có thể trỏ đến Triple Indirect Block để mở rộng khả năng ánh xạ tối đa cho các tập tin khổng lồ.

Hệ thống con trỏ này đảm bảo rằng mọi tập tin, dù lớn hay nhỏ, đều có thể tìm thấy dữ liệu của mình một cách có cấu trúc thông qua i-node.

# Cấu Trúc Thư mục (Directory Structure)
## Phân khu và Tổ chức (Partitioning and Organization)
Để quản lý hàng triệu tập tin trên các đĩa có dung lượng lớn, hệ thống cần tổ chức dữ liệu:
- **Phân khu (Partition/Volume)**: Là cấu trúc cấp thấp chia một đĩa thành nhiều vùng riêng biệt, mỗi vùng được xem là một thiết bị lưu trữ độc lập (đĩa ảo). Phân khu chứa thông tin về các tập tin bên trong nó, thường được giữ trong một **Thư mục Thiết bị** (Directory) hay **Bảng Mục lục Phân vùng** (Volume Table of Contents).
- **Thư mục (Directory)**: Có thể được xem là một **bảng danh mục** có nhiệm vụ dịch tên tập tin thành các mục từ thư mục tương ứng, cho phép chèn, xóa, tìm kiếm và liệt kê các tập tin.
## Các Mô hình Cấu trúc Thư mục
| Mô hình | Đặc điểm | Ưu điểm | Nhược điểm/Hạn chế |
|---------|----------|---------|-------------------|
| **Đơn cấp (Single-Level)** | Tất cả tập tin nằm trong cùng một thư mục. | Đơn giản nhất. | **Xung đột tên tập tin** khi nhiều người dùng sử dụng. Khó quản lý khi số lượng tập tin lớn. |
| **Hai cấp (Two-Level)** | Mỗi người dùng có một **Thư mục Tập tin Riêng (UFD). Thư mục Tập tin Chính (MFD)** lập chỉ mục UFD. | Cho phép người dùng khác nhau có tập tin trùng tên. | **Cô lập người dùng**, không thể chia sẻ tập tin. |
| **Dạng Cây (Tree-Structured)** | Là tổng quát của cấu trúc hai cấp. Cho phép người dùng tạo thư mục con (subdirectory). | Mỗi tập tin có tên **đường dẫn duy nhất**. Hỗ trợ tổ chức dữ liệu phân cấp, dễ quản lý hơn. | Ngăn cản việc chia sẻ tập tin và thư mục giữa các nhánh khác nhau của cây một cách trực tiếp. |
## Cấu trúc Chia sẻ (Sharing Structures)

Khi cần chia sẻ dữ liệu chung giữa người dùng, cấu trúc cây được mở rộng thành Đồ thị (Graph):

1. Đồ thị Không Chứa Chu trình (Acyclic Graph)
- Mục đích: Cho phép chia sẻ thư mục con và tập tin giữa nhiều thư mục khác nhau (ví dụ: giữa các UFD của thành viên trong nhóm).

- Cơ chế: Sử dụng Liên kết (Link) – một con trỏ chỉ tới tập tin hoặc thư mục con cần chia sẻ. Chỉ có một tập tin thực sự tồn tại, đảm bảo mọi thay đổi đều được người dùng khác nhìn thấy ngay lập tức.

+ Liên kết Cứng (Hard Link): Trong UNIX, được triển khai bằng cách tăng Số đếm Tham chiếu (Reference Count) trong i-node của tập tin gốc. Khi số đếm về 0, tập tin mới bị xóa khỏi đĩa.

+ Liên kết Biểu tượng (Symbolic Link / Soft Link): Là một tập tin chỉ chứa tên đường dẫn của tập tin/thư mục gốc. Việc xóa liên kết biểu tượng không ảnh hưởng đến tập tin nguồn. Tuy nhiên, nếu tập tin nguồn bị xóa, liên kết biểu tượng sẽ bị "chơi vơi" (dangling link).

2. Đồ thị Tổng quát (General Graph)
- Vấn đề: Khi sử dụng các liên kết (đặc biệt là liên kết biểu tượng) để liên kết một thư mục con trở lại một thư mục cha hoặc thư mục đã được duyệt trước đó, cấu trúc cây sẽ bị phá vỡ và hình thành chu trình (Cycle).

- Hạn chế: Sự tồn tại của chu trình làm phức tạp hóa quá trình duyệt thư mục và thu hồi không gian đĩa (Garbage Collection), vì vậy cấu trúc Đồ thị Không Chứa Chu trình được ưu tiên hơn trong hầu hết các hệ thống tập tin hiện đại.

# Cấu Trúc Phân Lớp của Hệ thống Tập tin (File System Structure)

- Ổ đĩa (Disk) là thiết bị lưu trữ chính vì khả năng đọc/ghi lại tại chỗ và khả năng truy xuất trực tiếp (random access) bất kỳ khối (block) thông tin nào. Để cải thiện hiệu suất I/O, quá trình truyền dữ liệu giữa bộ nhớ chính và đĩa được thực hiện theo đơn vị block (mỗi block chứa một hoặc nhiều sector, thường 512 byte/sector).

- Hệ thống tập tin (FS) được thiết kế để cung cấp tính thuận tiện và hiệu quả khi truy cập đĩa. FS giải quyết hai vấn đề cơ bản:

+ Cách FS hiển thị từ phía người dùng (tổ chức logic).
+ Cách ánh xạ hệ thống tập tin logic vào thiết bị lưu trữ vật lý (giải thuật và cấu trúc dữ liệu).

- FS được xây dựng theo mô hình phân cấp (layered model), với mỗi cấp tận dụng các tính năng của cấp thấp hơn.

## Các Cấp Độ Kiến Trúc File System

<img src="/images/theory/filesystem/disk-access-flow.png">

| Cấp độ | Vai trò chính | Chức năng chi tiết |
|--------|---------------|-------------------|
| **I/O Control (Điều khiển Nhập/Xuất)** | Chịu trách nhiệm chuyển thông tin giữa bộ nhớ chính và hệ thống đĩa. | Chứa Device Drivers (Bộ dịch lệnh cấp cao thành chỉ thị phần cứng) và các Bộ quản lý ngắt (Interrupt Handlers). |
| **Basic File System (FS Cơ bản)** | Phát ra lệnh I/O thông thường đến Device Driver để đọc/ghi khối vật lý (Physical Blocks). | Quản lý Memory Buffers và Caches để lưu trữ các khối dữ liệu, thư mục, metadata thường xuyên sử dụng, giúp tăng hiệu năng. |
| **File-Organization Module (FOM)** | Nhận biết các tệp (file), các khối logic (Logical Blocks) của chúng và ánh xạ tới khối vật lý (Physical Blocks). | Hiểu biết về cấp phát tệp và vị trí tệp. Chuyển dịch địa chỉ khối logic (0 → N) thành địa chỉ khối vật lý. Bao gồm Free-Space Manager (theo dõi và cung cấp các khối trống). |
| **Logical File System (FS Luận lý)** | Quản lý Metadata và Cấu trúc Thư mục để cung cấp cho FOM. | Duy trì cấu trúc tệp bằng cách sử dụng Khối Điều khiển Tệp (File Control Block - FCB) (gọi là i-node trong UNIX). FCB chứa thông tin về tệp (người sở hữu, quyền, vị trí nội dung). |