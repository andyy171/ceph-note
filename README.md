# Overview 
> Repo bao gồm các ghi chú về lý thuyết và thực hành cũng như kịch bản triển khai liên quan đến Ceph Storage .
>

# Repo structure
- `docs/` : Lý thuyết và các khái niệm quan trọng
- `labs/` : Các ghi chép về phần thực hành 
- `deployment-scenarios/` : Các kịch bản triển khai thực tế
- `issues-troubleshooting/` : Ghi chép về các lỗi trong quá trình học tập 
- `images/` : Hình ảnh minh họa 

<details>
<summary> Kiến thức cơ bản </summary>

<details>
<summary> Storage </summary>

### [Tổng quan về Storage](/docs/storage/01_overview.md)
</details>

<details>

<summary> File system </summary>

### [Tổng quan về Filesystem](https://github.com/andyy171/sys-oops-pewpew/blob/cb1506297c9e98ce866f8e623f934472a0d92d61/filesystem/01_overview_and_types.md)
### [Cấu trúc và Tổ chức thư mục ](https://github.com/andyy171/sys-oops-pewpew/blob/cb1506297c9e98ce866f8e623f934472a0d92d61/filesystem/02_structure_and_layout.md)
### [Quản lý truy cập & thực thi](https://github.com/andyy171/sys-oops-pewpew/blob/cb1506297c9e98ce866f8e623f934472a0d92d61/filesystem/03_access_control_and_fuse.md)
### [Quản lý bộ nhớ & I/O trong File System](https://github.com/andyy171/sys-oops-pewpew/blob/cb1506297c9e98ce866f8e623f934472a0d92d61/filesystem/04_memory_io_and_space_management.md)
### [Hiệu năng & Phục hồi](https://github.com/andyy171/sys-oops-pewpew/blob/cb1506297c9e98ce866f8e623f934472a0d92d61/filesystem/05_performance_and_recovery.md)
</details>
</details>

# Ceph Storage
## [Tổng quan kiến trúc Ceph](/docs/ceph/01-ceph-structure-overview.md)
## [Các khái niệm cốt lõi của Ceph](/docs/ceph/02-ceph-core-concepts.md)
## [Các lưu ý khi xây dựng Ceph Storage](/docs/ceph/03-ceph-planning-notes.md)
## [Các câu lệnh Ceph thông dụng](/docs/ceph/04-ceph-common-commands.md)
## [NVMe-oF với Ceph](/docs/ceph/13-ceph-nvme-of.md)

# Labs 
## [Triển khai Ceph 4-node](/labs/ceph-4-node-setup.md)