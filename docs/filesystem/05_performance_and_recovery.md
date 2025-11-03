# Nâng Cao Hiệu Năng Hệ Thống Tệp (FS Performance Enhancement)

Hiệu năng của hệ thống tệp được cải thiện đáng kể thông qua kỹ thuật caching ở nhiều cấp độ.

## Caching
- Cache của Disk Controller (Local Memory):
+ Disk controller thêm bộ nhớ nội tại để cache toàn bộ tracks.
+ Khi có yêu cầu tìm kiếm, track sẽ được đọc từ disk cache -> giảm thời gian chờ vật lý.
+ Block được yêu cầu sẽ được chuyển từ disk controller vào main memory (cache của OS).

## Các Kỹ Thuật Cache của Hệ Điều Hành (OS Cache)
Hệ điều hành sử dụng hai loại cache chính trong bộ nhớ chính:
| Logi | Cơ chế | Mục đích |
|------|--------|----------|
| **Buffer** | Hệ thống duy trì các phần khác nhau trong memory. Các block được lưu theo tần số sử dụng với thời gian ngắn. | Cache các block vật lý, thường là các block metadata của FS. |
| **Cache** | Sử dụng kỹ thuật Virtual Memory. Lưu lại file data dưới dạng pages (thay vì blocks). | Caching file data bằng địa chỉ ảo (virtual address) → hiệu năng cao hơn. |

**Ưu điểm:**Caching file data sử dụng địa chỉ ảo (Page Cache) đem lại hiệu năng cao hơn so với cache physical blocks (Buffer Cache).

## Kỹ Thuật Bộ Nhớ Ảo Hợp Nhất (Unified Virtual Memory - Unified Buffer Cache)
- Các OS mới nhất (như Unix/Linux) hỗ trợ kỹ thuật **Unified Virtual Memory** (cung cấp bởi **Unified Buffer Cache**).
- Mục tiêu: Sử dụng chung Page Cache -> giảm thiểu hiện tượng *double caching*.
- Double Caching: Xảy ra khi FS data được lưu hai lần (tại cả Page Cache và Buffer Cache) -> lãng phí tài nguyên hệ thống.
<img src="/images/theory/filesystem/double-cache.png">

- Hoạt động:
+ Sử dụng Memory Mapping (ánh xạ bộ nhớ).
+ Hoạt động đọc disk block bởi FS (ví dụ: block metadata) sẽ được cache trong Buffer Cache.
+ Hàm hệ thống chuẩn read() và write() sử dụng chung trên Page Cache.
<img src="/images/theory/filesystem/unified-cache.png">

## Vấn Đề Ảnh Hưởng đến Hiệu Năng: Đồng Bộ và Bất Đồng Bộ
| Loại Hoạt Động Ghi | Cơ chế | Ảnh hưởng Hiệu năng |
|-------------------|--------|-------------------|
| **Synchronous Writes (Ghi Đồng Bộ)** | Quá trình diễn ra **trực tiếp tới disk**. Sẽ không được lưu lại bộ đệm (cache). | Ảnh hưởng tiêu cực: không thể nhiều hơn một tiến trình sử dụng. Thường dùng cho các hoạt động cần độ tin cậy cao (ví dụ: chỉnh sửa metadata). |
| **Asynchronous Writes (Ghi Bất Đồng Bộ)** | Data sẽ được **cache lại** trước khi đồng bộ xuống disk. | Nâng cao hiệu năng vì hầu hết hoạt động đọc/ghi sử dụng kỹ thuật này. |

## Cải Thiện Tương Tác Cache, FS, Disk Driver
- Khi data được ghi tới disk, page được lưu vào cache.
- **Disk driver** sắp xếp đầu ra hàng đợi theo **disk address**.
- Hoạt động này cho phép Disk driver **tối ưu hóa việc di chuyển đầu đọc** tìm kiếm và ghi data (vì queue được tối ưu theo vòng quay/vị trí vật lý) -> giảm độ trễ truy cập.

# Khôi Phục Hệ Thống Tệp (File System Recovery)

Khi có lỗi, FS cần có khả năng khôi phục dữ liệu và tính nhất quán.

## Giới Thiệu và Vấn Đề
- **Nguyên nhân lỗi**: Xung đột trên FS data (directory structures, free-block pointers, FCBs, v.v.).
- **Vấn đề Caching**: Lỗi phổ biến xảy ra do tính năng caching. Một số thay đổi đã xuống disk, một số **còn nằm trong cache**. Nếu hệ thống lỗi trước khi cache kịp đưa xuống disk -> **xảy ra lỗi về data đang xử lý** (mất tính nhất quán).

## Các Phương Pháp Khôi Phục
### Consistency Checking (Kiểm tra Tính Nhất Quán)
- **Mục đích**: Khi xảy ra lỗi, chương trình hệ thống sẽ tìm kiếm và sửa lỗi.
- **Cơ chế**:
+ **Scan toàn bộ metadata** trên mỗi file và kiểm tra tính nhất quán hệ thống.
+ Quá trình này diễn ra **rất lâu**, thường xảy ra khi hệ thống khởi động lại.
- **Chương trình**: `fsck` (Unix) -> đối chiếu data trong directory structure với data block trên disk, cố gắng sửa các mâu thuẫn.
- **Phòng ngừa**: Đối với các hoạt động có thể gây lỗi cao, Unix sử dụng cơ chế ghi đồng bộ để tránh lỗi không thể sửa.

### Log-Structured File Systems (Hệ thống Tệp Dựa trên Log/Journaling)
- **Mục đích**: Giải quyết các vấn đề về thời gian và độ phức tạp của Consistency Checking.
- **Cơ chế (Log-based Transaction-Oriented/Journaling)**:
+ Tất cả thay đổi **metadata** được ghi tuần tự tới **Log (Journal)**. Một tập hợp các hoạt động được gọi là **Transaction**.
+ Khi thay đổi được ghi vào log, chúng được coi là **"committed"** (hệ thống có thể trả lại user process).
+ **Log Entry** sẽ lưu lại hoạt động thực sự sẽ diễn ra trên FS structure.
+ Khi Transaction hoàn thành -> Log entry sẽ được xóa khỏi log file (sử dụng circular buffer để ghi đè lên giá trị cũ).
- **Khôi phục (Sau khi Hệ thống Lỗi)**:
+ **Transaction đã Committed nhưng chưa hoàn thành**: Log sẽ tồn tại các nhiệm vụ chưa hoàn thành. Hệ thống sẽ tiếp tục thực hiện các nhiệm vụ này (Redo).
+ **Transaction bị Hủy (chưa Committed)**: Mọi hoạt động sẽ bị loại bỏ, khôi phục trạng thái ban đầu (Undo).