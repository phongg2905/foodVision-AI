# Thiết kế hệ thống suy luận, xếp hạng và cá nhân hóa gợi ý món ăn

**Mã:** `FV-REC-001` · **Phiên bản:** `1.0.0` · **Trạng thái:** Approved Baseline · **Phạm vi kỹ thuật:** Hợp đồng MVP (`Scoring v1.0`, [`ADR-008`](../07-decisions/ADR-008-pantry-ingredients-handling.md)) & Kiến trúc thông minh mở rộng (`Scoring v1.1` — Thành phần 04, 05, 06, 07, 08, 09, 10, 12, 14).

## 1. Phân lớp lộ trình thuật toán và tính tương thích hợp đồng API

Để vừa đảm bảo hợp đồng MVP (`P0`) chặt chẽ với [`openapi.yaml`](../03-api/openapi.yaml) hiện hành, vừa triển khai đầy đủ kiến trúc hệ thống thông minh đa tầng qua 5 giai đoạn, mô-đun gợi ý được tổ chức thành 2 chế độ tương thích ngược:

- **Chế độ chuẩn MVP (`Scoring v1.0` — Chặng `P0` hiện hành trong `openapi.yaml`):** nhận `(ingredient_ids, excluded_pantry_ids)`, phân 2 nhóm `availability` (`"ready"` và `"missing"`), chấm điểm quy tắc 4 thành phần `E, C, T, P` (`S = 89.0` khi đủ gia vị nền; `S = 68.1` khi thiếu gia vị bắt buộc).
- **Chế độ thông minh mở rộng (`Scoring v1.1` — Giai đoạn 2–5):** mở rộng sang suy luận thế giới mở 3 trạng thái nguyên liệu (`confirmed_available`, `confirmed_missing`, `unknown`) + lọc cứng dị ứng/thiết bị (`BLOCKED`), độ phủ có trọng số vai trò theo món ($C$), chấm điểm đa tiêu chí MCDA 5 thành phần ($S_{\text{base}} = 80.83$) kèm phân rã tuyến tính XAI, cá nhân hóa Logistic Regression ($p_{u,r}$), đa dạng hóa Top-K bằng MMR và đối chứng thực nghiệm với Tversky Similarity (Baseline B). *(Khi nâng cấp endpoint sang schema `v1.1` ở PR mã nguồn Giai đoạn 2–4, `openapi.yaml` sẽ được bổ sung các trường mở rộng tương ứng theo `NFR-10`).*

---

## 2. Đầu vào, nguồn sự thật và quy tắc gia vị nền (`BR-04`, `BR-07`, [`ADR-008`](../07-decisions/ADR-008-pantry-ingredients-handling.md))

Nguồn dữ liệu duy nhất đại diện cho nguyên liệu người dùng có khi tính điểm gợi ý là danh sách UUID **sau khi người dùng đã xác nhận/chỉnh sửa trên giao diện HITL** (từ kết quả YOLO/CLIP hoặc tìm kiếm tiếng Việt thủ công); không dùng trực tiếp `confidence` thô của YOLO làm xác suất sở hữu nguyên liệu.

```json
{
  "ingredient_ids": ["11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"],
  "excluded_pantry_ids": [],
  "max_total_minutes": 15,
  "cuisine_codes": ["VN"],
  "preferred_cuisine_codes": [],
  "include_missing": true,
  "limit": 20,
  "scan_id": null
}
```

- `Pantry`: tập 5 gia vị nền gia dụng có `category = 'pantry'` (**muối, đường, nước mắm, dầu ăn, tiêu xay**; nước lọc sinh hoạt không tạo bản ghi trong bảng `ingredients`). Mặc định thanh gia vị trên UI được bật sẵn (`checked`).
- `U = set(ingredient_ids)`: tập nguyên liệu chính người dùng xác nhận đang có (`category != 'pantry'`, `|U| >= 1`).
- `X = set(excluded_pantry_ids)`: tập gia vị nền người dùng chủ động bỏ chọn vì đang hết trong bếp (`X ⊆ Pantry`, mặc định `[]`). Gửi UUID `pantry` trong `ingredient_ids`, gửi nguyên liệu chính trong `excluded_pantry_ids`, hoặc gửi UUID không tồn tại/`is_active = false` sẽ bị chặn với `422 INVALID_INGREDIENTS`.
- `scan_id`: chỉ dùng để cập nhật bảng `scan_ingredients` khi `User` đã đăng nhập và bật `save_history = true`; nếu `scan_id` không tồn tại hoặc thuộc người dùng khác trả `404 SCAN_NOT_OWNED`; **không ảnh hưởng công thức tính điểm**.

---

## 3. Hợp đồng chấm điểm quy tắc MVP (`Scoring v1.0` — Khớp `openapi.yaml`)

Với mỗi công thức `r` đang ở trạng thái `published`, gọi `R_main = R_r \ Pantry` (`|R_main| >= 1` theo `BR-01`), `O_main = O_r \ Pantry`, `R_pantry = R_r ∩ Pantry` và `M_pantry = R_pantry ∩ X` (tập gia vị nền bắt buộc mà người dùng báo thiếu). Gia vị nền tùy chọn (`O_r ∩ Pantry`) không đưa vào tử số và mẫu số để tránh làm phình điểm `C` giả tạo. Chỉ xét các công thức khớp ít nhất 1 nguyên liệu chính (`|(R_main ∪ O_main) ∩ U| >= 1`, tức `C > 0`):

- **Độ phủ nguyên liệu bắt buộc `E`:**
  ```text
  E(r, U, X) = |R_main ∩ U| / (|R_main| + |M_pantry|)
  ```
- **Độ phủ nguyên liệu tổng hợp `C`:**
  ```text
  C(r, U, X) = (|R_main ∩ U| + 0.5 * |O_main ∩ U|) / (|R_main| + 0.5 * |O_main| + |M_pantry|)
  ```
- **Mức phù hợp thời gian `T`** (với `t = prep_minutes + cook_minutes`, trong đó `cook_minutes` đã gồm thời gian ướp/chờ/hầm bắt buộc theo `BR-05`; nếu đặt `max_total_minutes` thì món `t > max_total_minutes` bị loại cứng trước khi chấm):
  ```text
  T(r) = max(0.0, min(1.0, (60.0 - t) / 45.0))
  ```
- **Mức phù hợp nhóm ẩm thực mềm `P`:** `P(r) = 1.0` khi `preferred_cuisine_codes` rỗng hoặc `r.cuisine_code` thuộc `preferred_cuisine_codes`; ngược lại `P(r) = 0.0`.
- **Điểm tổng MVP `S` và quy tắc xếp hạng:**
  ```text
  S(r, U, X) = round(100.0 * (0.55 * C + 0.25 * E + 0.10 * T + 0.10 * P), 1)
  ```
  - `availability = "ready"` khi và chỉ khi `|R_main - U| = 0` và `|M_pantry| = 0` (`E = 1.0`); ngược lại `availability = "missing"` với `missing_required_ingredient_ids = sorted((R_main - U) ∪ M_pantry)`.
  - Xếp nhóm `"ready"` trước `"missing"`, trong từng nhóm sắp theo `score DESC`, `len(missing_required_ingredient_ids) ASC`, `total_minutes ASC`, `recipe_id ASC`.
  - **Ví dụ kiểm chứng chuẩn MVP ("Trứng xào cà chua": `R_main = {trứng gà, cà chua}`, `O_main = {hành lá}`, `R_pantry = {dầu ăn, nước mắm}`, `t = 5 + 8 = 13` phút, `U = {trứng gà, cà chua}`):**
    1. *Đủ gia vị nền (`X = []`):* `E = 2/2 = 1.0`, `C = 2/2.5 = 0.8`, `T = 1.0`, `P = 1.0` $\implies$ `S = 89.0`, `availability = "ready"` (nếu có thêm hành lá thì `C = 1.0`, `S = 100.0`).
    2. *Bỏ chọn Nước mắm (`X = [nuoc_mam_id]`):* `M_pantry = {nước mắm}`, `E = 2/3 ≈ 0.667`, `C = 2/3.5 ≈ 0.571`, `T = 1.0`, `P = 1.0` $\implies$ `S = 68.1`, `availability = "missing"`, `missing_required_ingredient_ids = [nuoc_mam_id]`.

---

## 4. Truy xuất kiểm duyệt & Suy luận luật ba trạng thái (Thành phần 10 & Thành phần 04 — `Scoring v1.1`)

### 4.1. Truy xuất công thức đã kiểm duyệt (Verified Recipe Retrieval — Thành phần 10)

Để loại bỏ rủi ro "ảo giác" định lượng hoặc bịa bước chế biến, hệ thống chỉ truy xuất các công thức có cấu trúc đã được Admin kiểm duyệt (`status = 'published'`, ký hiệu $\text{Verified}(r) = 1$) và chứa ít nhất một nguyên liệu chính truy vấn $q \in U$:

\[
R_q = \{r \in R : \text{Verified}(r) = 1 \land q \in \text{Ingredients}(r)\}
\]

### 4.2. Nguyên tắc Thế giới mở và suy luận 3 trạng thái nguyên liệu (Thành phần 04)

Việc một nguyên liệu không xuất hiện trong bức ảnh chụp **không đồng nghĩa** người dùng không có nguyên liệu đó trong bếp (Open-World Assumption). Ở chế độ thông minh `v1.1`, mỗi nguyên liệu $i$ mang một trong **ba trạng thái dữ kiện**:

- `confirmed_available` ($\text{Available}_u(i) = \text{True}$): nguyên liệu chính nằm trong `ingredient_ids` ($U$) **hoặc** gia vị nền `pantry` đang bật ($\text{Pantry} \setminus X$).
- `confirmed_missing` ($\text{Available}_u(i) = \text{False}$): gia vị nền bị người dùng tắt trong `excluded_pantry_ids` ($X$) **hoặc** nguyên liệu chính người dùng chủ động đánh dấu không có (`missing_ingredient_ids`).
- `unknown` ($\text{Available}_u(i) = \text{None}$): nguyên liệu chính bắt buộc chưa được xác nhận có hay không (ví dụ người dùng chỉ chụp quả cà chua, chưa khai báo về trứng).

Điều kiện đủ nguyên liệu và điều kiện khả thi chế biến ngay của món $r$ được định nghĩa:

\[
\text{Ready}(r, u) = \bigwedge_{i \in \text{Required}(r)} \big(\text{Available}_u(i) = \text{True}\big), \qquad \text{Feasible}(r, u) = \text{Ready}(r, u) \land \text{EquipOK}(r, u) \land \text{DietOK}(r, u)
\]

- $\text{DietOK}(r, u)$: lọc cứng tác nhân dị ứng (`excluded_allergen_ids`) dựa trên bảng liên kết chuẩn đã kiểm duyệt (`ingredient_allergens`), **tuyệt đối không chỉ đối sánh chuỗi tên món**.
- $\text{EquipOK}(r, u)$: kiểm tra thiết bị nấu bắt buộc (`required_equipment`) nếu người dùng khai báo giới hạn thiết bị bếp.

Mỗi công thức ứng viên được phân vào đúng **1 trong 4 trạng thái suy luận**:

| Trạng thái suy luận (`v1.1`) | Ánh xạ về enum `v1.0` | Điều kiện logic | Hành vi hệ thống |
|---|---|---|---|
| `BLOCKED` | _(Loại bỏ)_ | Vi phạm $\text{DietOK}$, $\text{EquipOK}$, `cuisine_codes` hoặc $t_r > t^*$ (`max_total_minutes`) | **Loại ngay trước khi chấm điểm**; không bao giờ xuất hiện lại ở bước MMR |
| `READY` | `"ready"` | $\text{Feasible}(r, u) = \text{True}$ (100% nguyên liệu bắt buộc `True` + đạt thiết bị/dị ứng) | Gắn huy hiệu **"Nấu ngay"**; ưu tiên hiển thị nhóm đầu |
| `UNKNOWN` | `"missing"` | Đạt ràng buộc cứng, không có nguyên liệu bắt buộc nào `False`, nhưng còn $\ge 1$ nguyên liệu bắt buộc là `None` | Gắn huy hiệu **"Cần kiểm tra thêm nguyên liệu"** (**không gắn "Nấu ngay"**); liệt kê các nguyên liệu chưa xác nhận |
| `MISSING_CONFIRMED` | `"missing"` | Đạt ràng buộc cứng, có $\ge 1$ nguyên liệu bắt buộc xác nhận `False` (thuộc `missing_ingredient_ids` hoặc `M_pantry`) | Gắn huy hiệu **"Cần mua thêm"**; liệt kê rõ nguyên liệu/gia vị cần mua |

---

## 5. Độ đầy đủ có trọng số (Thành phần 05) và Baseline Tversky (Thành phần 06)

### 5.1. Weighted Ingredient Coverage (Thành phần 05)

Vai trò của một nguyên liệu phụ thuộc vào **từng món ăn cụ thể** (cà chua là nguyên liệu chính của sốt cà chua nhưng chỉ tạo màu phụ ở món khác). Gọi $A = U \cup (\text{Pantry} \setminus X)$ là tập nguyên liệu xác nhận đang có và $w_{r,i} > 0$ là trọng số vai trò của nguyên liệu $i$ trong công thức $r$ (thang vai trò thử nghiệm: `primary` $= 4$, `essential` $= 3$, `secondary`/gia vị $= 1$):

\[
C(r, A) = \frac{\sum_{i \in R_r} w_{r,i} x_i}{\sum_{i \in R_r} w_{r,i}} \in [0, 1]
\]

Trong đó $x_i = 1$ nếu $i \in A$ (`confirmed_available`), và $x_i = 0$ trong phép tính điểm nếu nguyên liệu ở trạng thái `confirmed_missing` (bao gồm gia vị `pantry` bị tắt trong $X$) hoặc `unknown` (sự khác biệt ngữ nghĩa giữa `UNKNOWN` và `MISSING_CONFIRMED` được bảo toàn ở Mục 4.2).

### 5.2. Tversky Similarity — Thuật toán đối chứng Baseline B (Thành phần 06)

Theo mô hình tương đồng đặc trưng bất đối xứng của Amos Tversky (*Psychological Review*, 1977), hệ số tương đồng giữa tập nguyên liệu xác nhận có $A$ và tập nguyên liệu công thức cần $R_r$ là:

\[
T_{\alpha, \beta}(A, R_r) = \frac{|A \cap R_r|}{|A \cap R_r| + \alpha |A \setminus R_r| + \beta |R_r \setminus A|} \in [0, 1]
\]

Chọn $\beta > \alpha$ (ví dụ $\alpha = 0.3, \beta = 2.0$) để phạt việc thiếu nguyên liệu của món ăn mạnh hơn việc dư nguyên liệu khác trong bếp (khi $\alpha = \beta = 1$, công thức suy biến về hệ số Jaccard). **Nguyên tắc học thuật:** Tversky đóng vai trò **Baseline toán học (Phiên bản B)** để đối chứng thực nghiệm ở Mục 9; **tuyệt đối không cộng đồng thời cả $C(r, A)$ lẫn Tversky vào cùng một hàm điểm** nhằm tránh tính trùng lặp hai lần yếu tố độ phủ nguyên liệu.

---

## 6. Xếp hạng đa tiêu chí MCDA (Thành phần 07) & Giải thích điểm XAI (Thành phần 14)

### 6.1. Hàm điểm tổng hợp 5 tiêu chí ($S_{\text{base}}$)

Các công thức hợp lệ (không bị `BLOCKED` và khớp ít nhất 1 nguyên liệu chính) được chấm điểm theo Multi-Criteria Decision Analysis (MCDA) với 5 tiêu chí chuẩn hóa về `[0, 1]`:

\[
\boxed{S_{\text{base}}(r) = 100 \times (0.50\,C + 0.25\,G + 0.15\,T + 0.05\,P + 0.05\,Q)}
\]

1. **$C \in [0, 1]$ (`50%`) — Độ đầy đủ nguyên liệu có trọng số:** tính theo Mục 5.1.
2. **$G \in [0, 1]$ (`25%`) — Vai trò nguyên liệu trọng tâm:** bằng `1.0` nếu ít nhất một nguyên liệu người dùng vừa quét/chọn trọng tâm đóng vai trò `role = 'primary'` trong món $r$; nhận `0.5` nếu là `essential`, và `0.0` nếu chỉ là thành phần phụ.
3. **$T \in [0, 1]$ (`15%`) — Mức phù hợp thời gian mềm:** với $t_r = \text{prep\_minutes} + \text{cook\_minutes} > 0$ và mốc thời gian tham chiếu $t^*$ (mặc định $t^* = 15$ phút hoặc theo ngưỡng mong muốn):
   \[
   T(r) = \min\!\left(1, \frac{t^*}{t_r}\right), \quad t_r > 0
   \]
   *(Nếu bật lọc cứng `max_total_minutes`, mọi món có $t_r > \text{max\_total\_minutes}$ đã bị `BLOCKED` trước bước này).*
4. **$P \in [0, 1]$ (`5%`) — Mức khớp sở thích ban đầu:** khởi tạo trung lập $P = 0.5$ khi không chọn ưu tiên mềm (`1.0` nếu khớp `preferred_cuisine_codes`, `0.0` nếu lệch nhóm ưu tiên mềm).
5. **$Q \in [0, 1]$ (`5%`) — Chất lượng và độ tin cậy nguồn công thức:** đo mức hoàn thiện kiểm duyệt (`Q = 1.0` khi công thức có nguồn xác minh, đủ bước và định lượng chuẩn).

### 6.2. Phân rã điểm giải thích được — Score Breakdown XAI (Thành phần 14)

Do $S_{\text{base}} = 100 \sum_{k=1}^{5} w_k f_k$ là tổ hợp tuyến tính, đóng góp chính xác của từng tiêu chí thứ $k$ được tính trực tiếp (không cần xấp xỉ hộp đen):

\[
\text{Contribution}_k = 100 \, w_k f_k, \qquad \sum_{k=1}^{5} \text{Contribution}_k = S_{\text{base}}
\]

### 6.3. Ví dụ tính tay xuyên suốt ("Cà chua xào trứng")

- **Dữ kiện:** người dùng tải ảnh 1 quả cà chua (`U = {cà chua}`), thanh gia vị sẵn có bật `dầu ăn`, `muối` (`X = []`), **chưa khai báo có trứng hay không** (`trứng = None`). Công thức có $t_r = 13 \le 15 \implies T = 1.0$, cà chua là `primary` ($G = 1.0$), chưa đặt ưu tiên mềm ($P = 0.5$), đã kiểm duyệt đầy đủ ($Q = 1.0$).
- **Suy luận (Mục 4.2):** trạng thái = `UNKNOWN` (*"Cần kiểm tra thêm trứng gà — không gắn nhãn Nấu ngay"*).
- **Weighted Coverage (Mục 5.1):** trọng số `cà chua = 4`, `trứng = 3`, `dầu ăn = 1`, `muối = 1` (tổng $= 9$). Đang xác nhận có `4 + 1 + 1 = 6` $\implies C = 6/9 \approx 0.667$. *(Nếu người dùng tắt thêm `muối` trong `excluded_pantry_ids`, `muối` chuyển sang `False`, trạng thái thành `MISSING_CONFIRMED` và $C = 5/9 \approx 0.556$).*
- **Đối chứng Tversky Baseline B ($\alpha = 0.3, \beta = 2.0$):** $|A \cap R_r| = 3$, $|A \setminus R_r| = 0$, $|R_r \setminus A| = 1 \implies T_{0.3, 2.0} = \frac{3}{3 + 0.3(0) + 2.0(1)} = 0.60$.
- **Bảng phân rã MCDA & XAI:**

| Tiêu chí ($k$) | Phép tính $100 \times w_k \times f_k$ | Điểm đóng góp ($\text{Contribution}_k$) |
|---|---|---:|
| Độ đầy đủ nguyên liệu ($C$) | $100 \times 0.50 \times (6/9)$ | `33.33` |
| Vai trò nguyên liệu chính ($G$) | $100 \times 0.25 \times 1.0$ | `25.00` |
| Thời gian chế biến ($T$) | $100 \times 0.15 \times 1.0$ | `15.00` |
| Sở thích mặc định ($P$) | $100 \times 0.05 \times 0.5$ | `2.50` |
| Chất lượng công thức ($Q$) | $100 \times 0.05 \times 1.0$ | `5.00` |
| **Tổng ($S_{\text{base}}$)** | | **`80.83` / 100** |

---

## 7. Cá nhân hóa bằng Logistic Regression (Thành phần 08) & Đa dạng hóa MMR (Thành phần 09)

### 7.1. Học sở thích cá nhân hóa với Logistic Regression (Thành phần 08)

Ở Giai đoạn 4 (`P1`), hệ thống dự đoán xác suất người dùng đã đăng nhập $u$ phản hồi tích cực ($y = 1$) đối với món $r$ trên vector đặc trưng cố định chiều $x_r = [x_{\text{viet}}, x_{\text{canh}}, x_{\text{xao}}, x_{\text{time}}, x_{\text{coverage}}, \dots]^T$ (dùng chung cấu trúc chiều cho cả món `VN`, `EU`, `US`):

\[
p_{u,r} = P(y = 1 \mid u, r) = \sigma(\theta_u^T x_r) = \frac{1}{1 + e^{-\theta_u^T x_r}}, \qquad \theta_u^{\text{new}} = \theta_u^{\text{old}} + \eta (y - p_{u,r}) x_r
\]

- **Quy tắc nhãn phản hồi & chống lệch trọng số ([`ADR-012`](../07-decisions/ADR-012-feedback-uniqueness-and-context.md)):** chỉ cập nhật từ phản hồi tường minh hợp lệ (như lưu `favorites` hoặc `recommendation_feedback`; không gán $y = 0$ tùy tiện cho lượt chỉ cuộn lướt). Vì bảng `recommendation_feedback` dùng khóa `UNIQUE NULLS NOT DISTINCT (user_id, recipe_id, scan_session_id)`, khi huấn luyện hoặc tổng hợp thống kê cho mỗi cặp `(user_id, recipe_id)`, hệ thống chỉ lấy **1 bản ghi có `updated_at` mới nhất** để tránh lặp trọng số giữa các phiên quét.
- **Trộn điểm có kiểm soát Cold-Start:**
  \[
  S_{\text{final}}(u, r) = (1 - \lambda_{\text{pers}})\,S_{\text{base}}(r) + 100\,\lambda_{\text{pers}}\,p_{u,r}, \quad 0 \le \lambda_{\text{pers}} \le 1
  \]
  Với `Guest` hoặc `User` mới ít tương tác, đặt $\lambda_{\text{pers}} = 0$ ($S_{\text{final}} = S_{\text{base}}$); chỉ tăng $\lambda_{\text{pers}}$ khi đủ số lượng phản hồi và đạt kiểm định offline. Quá trình cập nhật $\theta_u$ hoàn toàn tách biệt với trọng số mô hình thị giác YOLO.

### 7.2. Đa dạng hóa danh sách Top-K bằng MMR (Thành phần 09)

Để tránh việc 5 kết quả đầu tiên toàn các biến thể gần trùng nhau (ví dụ 5 món canh cà chua), thuật toán **Maximal Marginal Relevance** (Carbonell & Goldstein, *SIGIR*, 1998) chọn lặp từng món vào tập kết quả $D$ từ các ứng viên hợp lệ:

\[
\text{MMR}(r) = \lambda_{\text{mmr}} \, \text{Rel}(r) - (1 - \lambda_{\text{mmr}}) \max_{s \in D} \text{Sim}(r, s)
\]

Với $\text{Rel}(r) = S_{\text{final}}(u, r) / 100 \in [0, 1]$, $\text{Sim}(r, s) \in [0, 1]$ đo độ tương đồng giữa hai công thức (theo phương pháp chế biến, nhóm ẩm thực và tập nguyên liệu), và mặc định thử nghiệm $\lambda_{\text{mmr}} = 0.7$:

- **Ví dụ tính tay ($D$ đã chọn `"Canh cà chua"`):**
  - `"Canh cà chua biến thể"` ($\text{Rel} = 0.91, \text{Sim} = 0.75$): $\text{MMR} = 0.7(0.91) - 0.3(0.75) = 0.412$.
  - `"Mì Ý sốt cà chua"` ($\text{Rel} = 0.88, \text{Sim} = 0.20$): $\text{MMR} = 0.7(0.88) - 0.3(0.20) = 0.556 \implies$ được ưu tiên chọn vào Top-K nhờ tính đa dạng.
- **Bất biến an toàn:** MMR chỉ tái sắp xếp các ứng viên hợp lệ trong cùng bậc ưu tiên khả thi, **tuyệt đối không bao giờ đưa các món đã bị `BLOCKED` (vi phạm dị ứng, thiết bị, thời gian hoặc ẩm thực cứng) quay trở lại danh sách**.

---

## 8. Pseudocode tham chiếu

```python
def infer_state_and_score_mcda(
    recipe,
    main_ids_confirmed,
    pantry_ids_all,
    excluded_pantry_ids=None,
    explicit_missing_main_ids=None,
    excluded_allergens=None,
    available_equipment=None,
    focus_ids=None,
    max_total_minutes=None,
    cuisine_codes=None,
    ref_minutes=15,
    P=0.5,
):
    U = set(main_ids_confirmed)
    X = set(excluded_pantry_ids or [])
    M_main = set(explicit_missing_main_ids or [])
    allergens = set(excluded_allergens or [])

    if recipe.status != "published" or not recipe.required_main_ids:
        return "BLOCKED", None
    if cuisine_codes and recipe.cuisine_code not in cuisine_codes:
        return "BLOCKED", None
    total_min = recipe.prep_minutes + recipe.cook_minutes
    if max_total_minutes is not None and total_min > max_total_minutes:
        return "BLOCKED", None
    if recipe.allergen_ids & allergens:
        return "BLOCKED", None
    if available_equipment is not None and not recipe.required_equipment.issubset(available_equipment):
        return "BLOCKED", None
    if not ((recipe.required_main_ids | recipe.optional_main_ids) & U):
        return "BLOCKED", None

    confirmed_set = U | (set(pantry_ids_all) - X)
    missing_set = M_main | X

    has_missing = any(i in missing_set for i in recipe.required_all_ids)
    has_unknown = any(
        (i not in confirmed_set) and (i not in missing_set)
        for i in recipe.required_all_ids
    )
    state = "MISSING_CONFIRMED" if has_missing else ("UNKNOWN" if has_unknown else "READY")

    total_w = sum(recipe.weights.values())
    matched_w = sum(w for ing_id, w in recipe.weights.items() if ing_id in confirmed_set)
    C = matched_w / total_w if total_w > 0 else 0.0
    focus = set(focus_ids or U)
    G = 1.0 if (recipe.primary_ids & focus) else (0.5 if (set(recipe.weights) & focus) else 0.0)
    T = min(1.0, ref_minutes / max(1, total_min))
    Q = recipe.quality_score

    w_mcda = {"C": 0.50, "G": 0.25, "T": 0.15, "P": 0.05, "Q": 0.05}
    feats = {"C": C, "G": G, "T": T, "P": P, "Q": Q}
    contribs = {k: round(100.0 * w_mcda[k] * feats[k], 2) for k in w_mcda}
    return state, {"score_base": round(sum(contribs.values()), 2), "features": feats, "contributions": contribs}
```

---

## 9. Đo lường và thiết kế đối chứng thực nghiệm (Thành phần 12)

Trên bộ tối thiểu **100 tình huống đầu vào** được người chấm độc lập gán nhãn mức độ phù hợp $\text{rel}_j \in \{0, 1, 2, 3\}$ trước khi chạy thuật toán (Järvelin & Kekäläinen, *ACM TOIS*, 2002):

\[
\text{Precision@5} = \frac{\text{số món phù hợp trong 5 kết quả đầu}}{5}, \qquad \text{DCG@5} = \sum_{j=1}^{5} \frac{2^{\text{rel}_j} - 1}{\log_2(j + 1)}, \qquad \text{nDCG@5} = \frac{\text{DCG@5}}{\text{IDCG@5}}
\]

| Phiên bản đối chứng | Cơ chế xếp hạng | Mục đích thực nghiệm |
|---|---|---|
| **A — Truy xuất đơn giản** | Chỉ lọc công thức `published` có chứa nguyên liệu khớp | Baseline thấp nhất |
| **B — Tversky Similarity** | So khớp tập hợp bất đối xứng $T_{\alpha,\beta}$ ($\alpha=0.3, \beta=2.0$) | Baseline toán học cổ điển (Thành phần 06) |
| **C — 3-State + Weighted + MCDA + MMR** | Suy luận 3 trạng thái, Weighted Coverage, MCDA 5 tiêu chí và MMR | Đo mức cải thiện của biểu diễn tri thức & quyết định đa tiêu chí |
| **D — Cá nhân hóa (C + Logistic Regression)** | Kết hợp Phiên bản C với xác suất sở thích $p_{u,r}$ | Đo đóng góp thực tế của học máy cá nhân hóa (Thành phần 08) |

**Nguyên tắc kiểm định nghiêm ngặt:** cả 4 phiên bản chạy trên cùng tập truy vấn, cùng kho công thức đã kiểm duyệt và cùng bộ nhãn đánh giá độc lập. Với Phiên bản D, bắt buộc **chia tập dữ liệu phản hồi theo mốc thời gian (temporal split)** để không rò rỉ tương tác tương lai vào quá trình huấn luyện, đồng thời báo cáo độ đa dạng Top-K và tỷ lệ vi phạm ràng buộc cứng (mục tiêu lọt tác nhân dị ứng đã khai báo = `0%`).
