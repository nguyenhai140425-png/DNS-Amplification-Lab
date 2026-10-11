# DNS Amplification Attack & Response Rate Limiting (RRL) Defense Lab

> **Target Role:** SOC Intern / Security Analyst  
> **Keywords:** DNS Amplification, IP Spoofing, UDP Reflection, Response Rate Limiting (RRL), BIND9, Scapy, Packet Analysis, Docker Network Isolation.

---

## 📌 Executive Summary

Bài project mô phỏng và phân tích kịch bản tấn công **DNS Amplification (Reflective DDoS)** trong môi trường Docker cô lập, đồng thời triển khai và đánh giá cơ chế phòng thủ **Response Rate Limiting (RRL)** trực tiếp trên máy chủ DNS BIND9. 

Dự án thể hiện tư duy phân tích lưu lượng mạng (Packet Analysis), hiểu biết sâu sắc về giao thức UDP/DNS, và khả năng cấu hình các giải pháp giảm thiểu rủi ro (Mitigation) cho hệ thống SOC/Blue Team.

---

## 🏗️ Architecture & Lab Setup

Mô hình phòng thí nghiệm được xây dựng hoàn toàn bằng **Docker Compose**, hoạt động trong mạng nội bộ cô lập (`172.20.0.0/24`), hoàn toàn tách biệt khỏi Internet.

```
       +-------------------------------------------------+
       |               Attacker (Kali)                   |
       |                 172.20.0.10                     |
       +-------------------------------------------------+
                                |
                                | [1] Spoofed DNS Request
                                |     (src: 172.20.0.30, qtype: TXT)
                                v
       +-------------------------------------------------+
       |           DNS Reflector (BIND9)                 |
       |                 172.20.0.20                     |
       +-------------------------------------------------+
                                |
                                | [2] Amplified DNS Response
                                |     (Length: ~878 - 906 bytes)
                                v
       +-------------------------------------------------+
       |                Victim (Kali)                    |
       |                 172.20.0.30                     |
       +-------------------------------------------------+
```

### Component Details
* **Attacker (`172.20.0.10`)**: Sử dụng Python (`Scapy`) để chế tạo gói tin UDP/DNS thô (Raw Packets) với địa chỉ IP nguồn giả mạo (`172.20.0.30`). Cần cấp cờ `NET_RAW` / `NET_ADMIN`.
* **Reflector (`172.20.0.20`)**: Máy chủ BIND9 đóng vai trò Authoritative DNS Server cho domain `lab.test`, chứa bản ghi `TXT` lớn (`big.lab.test`).
* **Victim (`172.20.0.30`)**: Nạn nhân hứng chịu toàn bộ lưu lượng phản hồi bị khuếch đại, tiến hành giám sát bằng `tcpdump`.

---

## 📂 Project Structure

```text
├── docker-compose.yml          # Cấu hình mạng 172.20.0.0/24 & container
├── attacker/
│   ├── Dockerfile             # Kali Linux base, cài đặt Scapy, tcpdump, dnsutils
│   └── script.py              # Script Scapy crafted UDP DNS request với IP Spoofing
├── reflector/
│   ├── Dockerfile             # BIND9 server container
│   ├── named.conf             # File cấu hình BIND9 (bao gồm cấu hình RRL)
│   └── db.lab.test            # Zone file chứa bản ghi TXT lớn (Amplification Vector)
└── victim/
    └── Dockerfile             # Environment cho victim giám sát lưu lượng
```

---

## 🚀 Attack Simulation & Packet Analysis

### 1. Kịch bản tấn công (Attack Execution)
Kẻ tấn công gửi truy vấn DNS dạng `TXT` tới bản ghi `big.lab.test` trên máy chủ BIND9. Do bản chất bất đối xứng của giao thức UDP và việc giả mạo IP nguồn:
* **Payload request ban đầu:** ~41 - 69 bytes.
* **Payload response trả về:** ~878 - 906 bytes.
* **Hệ số khuếch đại (Amplification Factor):** **~13x - 20x**.

### 2. Bắt gói tin (Packet Capture before Defense)
Sử dụng `tcpdump` trên máy chủ **Victim**:
```bash
tcpdump -ni any -vv 'udp port 53'
```
**Kết quả ghi nhận:**
```text
18:45:04.890953 eth0 In IP (tos 0x0, ttl 64, id 62211, offset 0, flags [none], proto UDP (17), length 906)
    172.20.0.20.53 > 172.20.0.30.11448: [bad udp cksum] q: TXT? big.lab.test. 1/1/2 ... OPT UDPsize=1232 DO (878)
```
*Gói tin phản hồi bị phình to đầy đủ dữ liệu TXT dài 878 bytes dội trực tiếp về phía nạn nhân.*

---

## 🛡️ Defensive Mechanism: BIND9 Response Rate Limiting (RRL)

### 1. Hạn chế của các biện pháp phòng thủ tĩnh
Các thiết lập BIND9 mặc định như `recursion no;` hay `max-udp-size 1232;` **không hiệu quả** trong kịch bản này vì:
* Kẻ tấn công truy vấn trực tiếp vào **Authoritative Zone** (`big.lab.test`) do Reflector quản lý, không kích hoạt tiến trình đệ quy (`recursion`).
* Kích thước gói phản hồi (~878 bytes) nằm dưới ngưỡng `max-udp-size 1232`.

### 2. Cấu hình Response Rate Limiting (RRL)
Tích hợp thuật toán RRL vào khối `options` trong `named.conf`:

```bind
rate-limit {
    responses-per-second 3;
    slip 2;
    window 5;
};
```

* **`responses-per-second 3`**: Hạn chế tối đa 3 phản hồi/giây cho cùng một mẫu truy vấn.
* **`window 5`**: Cửa sổ thời gian tính toán giới hạn là 5 giây.
* **`slip 2`**: Khi vượt ngưỡng, cứ mỗi 2 gói tin vượt mức, BIND9 sẽ hạ kích thước gói bằng cách xóa phần payload cồng kềnh, chỉ giữ lại tiêu đề tối thiểu kèm cờ cắt cụt **TC (Truncated Flag)**.

### 3. Phân tích kết quả sau khi bật RRL

Sau khi chạy lại kịch bản tấn công dồn dập (`for i in {1..30}; do python3 /lab/script.py & done`), quan sát qua `tcpdump`:

```text
03:28:26.602356 eth0 In IP (tos 0x0, ttl 64, id 37933, offset 0, flags [none], proto UDP (17), length 69)
    172.20.0.20.53 > 172.20.0.30.59211: [bad udp cksum] 0*|$ q: TXT? big.lab.test. 0/0/1 ar: OPT UDPsize=1232 DO (41)
```

**Đánh giá:**
* Sau khi hết hạn mức Burst ban đầu, BIND9 kích hoạt trạng thái lọc (`slip 2`).
* Kích thước gói tin phản hồi lập tức giảm từ **906 bytes (payload 878 bytes)** xuống còn **69 bytes**.
* Cờ `TC` được bật, triệt tiêu hoàn toàn hệ số khuếch đại băng thông của cuộc tấn công.

---

## 📊 Comparison Table

| Tiêu chí so sánh | Chưa bật RRL (Under Attack) | Đã bật RRL (Defensive State) |
| :--- | :--- | :--- |
| **Kích thước gói phản hồi** | ~878 - 906 bytes | **69 bytes** (kèm cờ TC) |
| **Hệ số khuếch đại** | Mức cao (~13x - 20x) | **Triệt tiêu về ~1x** |
| **Tác động đến Victim** | Nguy cơ nghẽn mạng do dội băng thông lớn | Dữ liệu dội về thu gọn tối đa, bảo vệ đường truyền |
| **Hành vi máy chủ DNS** | Phản hồi đầy đủ mọi request dồn dập | Kích hoạt giới hạn tần suất & hạ cấp gói tin |

---

## 💡 SOC/Security Analyst Evaluation

### Ưu điểm của RRL
* **Native Support:** Tích hợp trực tiếp trong BIND9, không tốn chi phí hạ tầng hay phần mềm bên thứ ba.
* **Cơ chế Truncation linh hoạt:** Sử dụng cờ TC thay vì Drop hoàn toàn gói tin, cho phép các Client hợp pháp có khả năng fallback chuyển sang giao thức TCP để truy vấn lại.

### Hạn chế & Góc nhìn SOC
* **Physical Bandwidth Exhaustion:** RRL vận hành ở tầng ứng dụng (L7). Nếu băng thông đường truyền (L3/L4) đến DNS Server bị bão hòa hoàn toàn bởi lượng request khổng lồ, RRL sẽ không giải quyết được ở cấp độ NIC.
* **False Positives:** Đòi hỏi fine-tuning các tham số (`responses-per-second`, `window`) phù hợp với baseline lưu lượng thực tế để tránh ảnh hưởng đến người dùng thật vào các khung giờ cao điểm.

---

## 🛠️ How to Run the Lab

1. **Khởi chạy môi trường:**
   ```bash
   docker compose up -d --build
   ```

2. **Kiểm tra kết nối giữa các container:**
   ```bash
   docker exec -it attacker ping 172.20.0.20
   docker exec -it attacker ping 172.20.0.30
   ```

3. **Lắng nghe gói tin tại máy Victim:**
   ```bash
   docker exec -it victim tcpdump -ni any -vv 'udp port 53'
   ```

4. **Thực thi tấn công từ máy Attacker:**
   ```bash
   docker exec -it attacker python3 /lab/script.py