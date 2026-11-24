# Thiết kế hệ thống suy luận, xếp hạng và cá nhân hóa gợi ý món ăn

**Mã:** `FV-REC-001` · **Phiên bản:** `1.1.0` · **Trạng thái:** Approved Baseline · **Phạm vi kỹ thuật:** Luồng HITL & Cá nhân hóa nguyên liệu ([`ADR-013`](../07-decisions/ADR-013-unified-mcda-and-ingredient-personalization.md), [`ADR-008`](../07-decisions/ADR-008-pantry-ingredients-handling.md), [`ADR-009`](../07-decisions/ADR-009-cooking-and-waiting-time.md)) — Thành phần `04, 05, 06, 07, 08, 09, 10, 12, 14`.

---

## 1. Dữ liệu cá nhân hóa và Luồng tương tác xuyên suốt

### 1.1. Hồ sơ dữ liệu cá nhân hóa theo nguyên liệu (`user_preferences`)

Mỗi người dùng đã đăng nhập (`User` / `Admin`) có thể thiết lập trước 3 danh sách cá nhân hóa gắn với thực thể chuẩn `ingredients.id` (khách `Guest` có thể truyền trực tiếp theo từng phiên gọi API):

1. **Nguyên liệu bị dị ứng (`allergic_ingredient_ids`):** dùng để **lọc cứng (`BLOCKED`)** tuyệt đối mọi công thức có chứa nguyên liệu gây dị ứng (kết hợp cùng nhóm tác nhân `excluded_allergen_ids` trên bảng `ingredient_allergens`).
2. **Gia vị có trong bếp (`kitchen_spice_ids`, thuộc `category = 'pantry'`):** danh sách gia vị nền đang có sẵn trong bếp của người dùng. Với `Guest` chưa cấu hình hồ sơ, hệ thống mặc định bật sẵn bộ 5 gia vị gia dụng cơ bản (**muối, đường, nước mắm, dầu ăn, tiêu xay**) và cho phép bật/tắt nhanh qua `excluded_pantry_ids`. Các gia vị đang có được tự động gộp vào tập xác nhận có $A$ để tính độ đủ nguyên liệu $C(r, A)$ (**không lọc cứng** món thiếu gia vị).
3. **Nguyên liệu yêu thích (`favorite_ingredient_ids`, tập $F_u$):** danh sách các nguyên liệu người dùng ưa thích, dùng trực tiếp để đo mức độ phù hợp sở thích $P(r)$.

### 1.2. Luồng 5 bước từ Scan ảnh đến Xếp hạng món ăn

1. **Scan ảnh $\to$ Phân tách nguyên liệu trong ảnh (`TP 01`, `TP 02`, `TP 14`):**
   - Sau khi xoay chuẩn `EXIF Orientation` và xóa sạch `EXIF/GPS` trong RAM, mô hình YOLO trả kết quả phát hiện được chia làm 2 nhóm trên giao diện:
     - **Nguyên liệu rõ (`clear_ingredients`):** các phát hiện có $\text{confidence} \ge \tau$ (mặc định $\tau = 0.80$), được tích chọn sẵn.
     - **Nguyên liệu không rõ (`uncertain_ingredients`):** các phát hiện có $\text{confidence} < \tau$ (`needs_confirmation = true`), hiển thị cảnh báo để **người dùng chủ động xác nhận** mới đưa vào danh sách có.
2. **Chuẩn hóa nguyên liệu $\to$ Sửa / Xóa / Thêm tùy chọn (`TP 13`):**
   - Toàn bộ nhãn nhận diện và từ khóa gõ tay (có dấu, không dấu, từ đồng nghĩa vùng miền qua `unaccent` + `pg_trgm`) được chuẩn hóa về UUID `ingredients.id` (`category != 'pantry'`). Người dùng có thể sửa, xóa, thêm nguyên liệu hoặc **Bỏ qua** để giữ nguyên tập nguyên liệu rõ đã nhận diện $U$ ($|U| \ge 1$).
3. **Chọn nguyên liệu chính mong muốn hoặc không (`main_ingredient_ids`):**
   - Người dùng tùy chọn đánh dấu một tập con $U_{\text{main}} \subseteq U$ làm nguyên liệu chính muốn ưu tiên chế biến (phần còn lại là $U_{\text{sub}} = U \setminus U_{\text{main}}$). **Mặc định là không chọn** ($U_{\text{main}} = \emptyset$, người dùng có thể **Bỏ qua**).
4. **Chọn thời gian nấu mong muốn $t^*$ (`desired_hours`):**
   - Đơn vị tính bằng **giờ (`hours`)**. Nếu người dùng không nhập, hệ thống đặt **mặc định $t^* = 100.0\text{ giờ}$**. Đây là mốc tham chiếu mềm dùng cho tiêu chí $T(r)$ (không lọc cứng để tránh làm $T(r) \equiv 1.0$; nếu người dùng chủ động bật bộ lọc nhanh trên giao diện thì truyền riêng `max_total_minutes`).
5. **Truy xuất công thức $\to$ Lọc dị ứng / Đối chiếu gia vị $\to$ Chấm điểm $S(r)$:**
   - Lọc các công thức `status = 'published'` có chứa **ít nhất 1 nguyên liệu** thuộc tập $U$.
   - Loại cứng (`BLOCKED`) các món vi phạm nguyên liệu dị ứng (`allergic_ingredient_ids` / `excluded_allergen_ids`) hoặc bộ lọc cứng tùy chọn (`cuisine_codes`, `max_total_minutes`).
   - Đối chiếu gia vị có trong bếp để xác lập tập nguyên liệu xác nhận đang có $A = U \cup S_{\text{bếp}}$, suy luận trạng thái và tính điểm $S(r)$ theo 4 tiêu chí `C, G, T, P`.

---

## 2. Hợp đồng đầu vào API gợi ý (`POST /api/v1/recommendations`)

```json
{
  "ingredient_ids": [
    "11111111-1111-4111-8111-111111111101",
    "11111111-1111-4111-8111-111111111102"
  ],
  "main_ingredient_ids": [],
  "desired_hours": 100.0,
  "allergic_ingredient_ids": [],
  "kitchen_spice_ids": null,
  "excluded_pantry_ids": [],
  "favorite_ingredient_ids": [],
  "max_total_minutes": null,
  "cuisine_codes": [],
  "include_missing": true,
  "diversify": false,
  "limit": 20,
  "scan_id": null
}
```

- `U = set(ingredient_ids)`: tập nguyên liệu người dùng xác nhận có (`category != 'pantry'`, `|U| >= 1`).
- `U_main = set(main_ingredient_ids)`: tập nguyên liệu chính người dùng chọn (`U_main ⊆ U`, mặc định `[]`). Nếu gửi UUID không nằm trong `ingredient_ids`, trả `422 INVALID_INGREDIENTS`.
- `S_bep`: nếu truyền `kitchen_spice_ids != null` (hồ sơ bếp cá nhân), $S_{\text{bếp}} = \text{set}(\text{kitchen\_spice\_ids}) \setminus X$; nếu `kitchen_spice_ids == null` (mặc định), $S_{\text{bếp}} = \text{Pantry} \setminus X$ với $X = \text{set}(\text{excluded\_pantry\_ids})$.
- `A = U ∪ S_bep`: tập toàn bộ nguyên liệu và gia vị người dùng xác nhận đang có.
- `diversify` (mặc định `false`): khi `false`, sắp xếp giảm dần thuần túy theo điểm tổng $S(r)$ của `ADR-013` để kiểm chứng toán học 100%; khi truyền `true` (hoặc chạy thực nghiệm Giai đoạn 5), áp dụng tái xếp hạng đa dạng hóa Top-K bằng MMR (`rerank_with_mmr`). Khi có Bearer token hợp lệ và các trường cá nhân hóa không bị ghi đè trong request, hệ thống tự động nạp hồ sơ đã lưu từ `user_preferences`.

---

## 3. Truy xuất kiểm duyệt & Suy luận luật ba trạng thái (Thành phần 10 & Thành phần 04)

### 3.1. Truy xuất công thức đã kiểm duyệt (Verified Recipe Retrieval — Thành phần 10)

Hệ thống chỉ truy xuất các công thức có cấu trúc đã được Admin kiểm duyệt (`status = 'published'`, $\text{Verified}(r) = 1$) và chứa ít nhất một nguyên liệu thuộc tập $U$:

\[
R_U = \{r \in R : \text{Verified}(r) = 1 \land (\text{Ingredients}_{\text{non-pantry}}(r) \cap U \ne \emptyset)\}
\]

### 3.2. Nguyên tắc Thế giới mở và suy luận 3 trạng thái nguyên liệu (Thành phần 04)

Việc một nguyên liệu không xuất hiện trong ảnh chụp **không đồng nghĩa** người dùng không có nó trong bếp (Open-World Assumption). Mỗi nguyên liệu bắt buộc $i \in R_r$ mang một trong **ba trạng thái dữ kiện**:

- `confirmed_available` ($\text{Available}_u(i) = \text{True}$): $i \in A$ (thuộc $U$ hoặc thuộc gia vị bếp đang có $S_{\text{bếp}}$).
- `confirmed_missing` ($\text{Available}_u(i) = \text{False}$): gia vị nền không có trong bếp ($\text{Pantry} \setminus S_{\text{bếp}}$) hoặc nguyên liệu người dùng chủ động đánh dấu không có (`missing_ingredient_ids`).
- `unknown` ($\text{Available}_u(i) = \text{None}$): nguyên liệu bắt buộc chưa được xác nhận có hay không.

Mỗi công thức ứng viên được phân vào đúng **1 trong 4 trạng thái suy luận**:

| Trạng thái suy luận (`status`) | Giá trị `availability` | Điều kiện logic | Hành vi hệ thống |
|---|---|---|---|
| `BLOCKED` | _(Loại bỏ)_ | Chứa nguyên liệu dị ứng (`allergic_ingredient_ids` / `excluded_allergen_ids`), sai `cuisine_codes` hoặc vượt `max_total_minutes` (khi bật lọc cứng) | **Loại ngay trước khi chấm điểm**; `0%` xuất hiện lại ở bước MMR |
| `READY` | `"ready"` | 100% nguyên liệu bắt buộc $i \in R_r$ ở trạng thái `confirmed_available` | Gắn huy hiệu **"Nấu ngay"**; ưu tiên xếp nhóm đầu |
| `UNKNOWN` | `"missing"` | Không bị `BLOCKED`, không có nguyên liệu bắt buộc nào `False`, nhưng còn $\ge 1$ nguyên liệu bắt buộc `None` | Gắn huy hiệu **"Cần kiểm tra thêm nguyên liệu"**; liệt kê nguyên liệu chưa xác nhận |
| `MISSING_CONFIRMED` | `"missing"` | Không bị `BLOCKED`, có $\ge 1$ nguyên liệu bắt buộc xác nhận `False` (thiếu gia vị bếp hoặc báo hết) | Gắn huy hiệu **"Cần mua thêm"**; liệt kê rõ nguyên liệu/gia vị thiếu |

---

## 4. Đặc tả Toán học 4 Tiêu chí Chấm điểm (`C, G, T, P`) & Hàm tổng `S`

### 4.1. Đo mức đủ của nguyên liệu — $C(r, A)$ (`50%`, Thành phần 05)

Mỗi nguyên liệu gắn với công thức $r$ trong bảng `recipe_ingredients` được phân loại theo mức độ ảnh hưởng đến bản chất món ăn để đặt trọng số $w_{r,i}$:

| Nhóm nguyên liệu (`role`) | Tiêu chí phân loại | Trọng số đề xuất ($w_{r,i}$) | Đưa vào tập bắt buộc $R_r$ |
|---|---|---:|---|
| **Nguyên liệu cốt lõi (`core`)** | Quyết định bản chất món ăn, thiếu sẽ không còn đúng công thức gốc | `4` | Có (`is_required = true`) |
| **Nguyên liệu phụ quan trọng (`secondary`)** | Có vai trò đáng kể nhưng không quyết định bản chất món | `2` | Có (`is_required = true`) |
| **Gia vị, nguyên liệu hỗ trợ (`spice`)** | Chủ yếu điều chỉnh hương vị hoặc hỗ trợ chế biến (gồm cả `pantry`) | `1` | Có (`is_required = true`) |
| **Nguyên liệu tùy chọn (`optional`)** | Có thể bỏ qua mà vẫn giữ công thức hợp lệ | `0` *(ngoài $R_r$)* | **Không** (`is_required = false`) |

Độ đủ nguyên liệu có trọng số của món $r$ trên tập xác nhận có $A$ được tính bởi:

\[
C(r, A) = \frac{\sum_{i \in R_r} w_{r,i} \, x_i}{\sum_{i \in R_r} w_{r,i}} \in [0, 1], \qquad \sum_{i \in R_r} w_{r,i} > 0
\]

Trong đó $w_{r,i} > 0$ với mọi $i \in R_r$; $x_i = 1$ nếu người dùng xác nhận có ($i \in A$), và $x_i = 0$ trong phép tính điểm nếu chưa xác nhận có (trạng thái gốc vẫn phân biệt rõ `"không có"` và `"chưa biết"` ở Mục 3.2).

*(Đối chứng học thuật — Thành phần 06: Hệ số bất đối xứng **Tversky Similarity** $T_{\alpha,\beta}(A, R_r) = \frac{|A \cap R_r|}{|A \cap R_r| + \alpha|A \setminus R_r| + \beta|R_r \setminus A|}$ với $\alpha = 0.3, \beta = 2.0$ được giữ độc lập làm **Baseline B** trong thực nghiệm Giai đoạn 5; tuyệt đối không cộng đồng thời vào hàm điểm cùng $C(r, A)$).*

### 4.2. Đo vai trò của nguyên liệu chính — $G(r)$ (`25%`, Thành phần 07)

Để phản ánh cả **vai trò nguyên liệu trong món ăn $r$** lẫn **ý định chọn nguyên liệu chính của người dùng** trên tập $U$:

1. **Tag vai trò nguyên liệu trong món ăn (`dish_role` lưu ở `recipe_ingredients`):**
   \[
   g(i, r) = \begin{cases}
   1.0, & \text{nếu } i \text{ mang tag nguyên liệu chính (`dish_role = 'main'`) trong món } r \\
   0.5, & \text{nếu } i \text{ mang tag nguyên liệu phụ (`dish_role = 'sub'`) có mặt trong món } r \\
   0.0, & \text{nếu } i \text{ không xuất hiện trong công thức } r
   \end{cases}
   \]
2. **Phân bổ trọng số nhóm chính / phụ phía người dùng ($w_{\text{chính}} = 0.7$, $w_{\text{phụ}} = 0.3$):**
   Với $U = U_{\text{main}} \cup U_{\text{sub}}$ ($U_{\text{main}} \cap U_{\text{sub}} = \emptyset$, $|U| \ge 1$), tổng trọng số nhóm nguyên liệu chính bằng `0.7` và tổng trọng số nhóm nguyên liệu phụ bằng `0.3`:
   \[
   w_i = \begin{cases}
   \dfrac{0.7}{|U_{\text{main}}|}, & \text{nếu } i \in U_{\text{main}} \\[8pt]
   \dfrac{0.3}{|U_{\text{sub}}|}, & \text{nếu } i \in U_{\text{sub}}
   \end{cases}
   \]
3. **Công thức tính $G(r)$:**
   \[
   G(r) = \frac{\sum_{i \in U} w_i \, g(i, r)}{\sum_{i \in U} w_i} \in [0, 1]
   \]
   - Khi người dùng có chọn cả chính và phụ ($U_{\text{main}} \ne \emptyset, U_{\text{sub}} \ne \emptyset$): $\sum_{i \in U} w_i = 0.7 + 0.3 = 1.0$.
   - Khi người dùng **bỏ qua không chọn nguyên liệu chính** (mặc định $U_{\text{main}} = \emptyset \implies U_{\text{sub}} = U$) hoặc chọn tất cả làm chính ($U_{\text{sub}} = \emptyset$): mọi $i \in U$ có cùng trọng số nên mẫu số luôn dương ($0.3$ hoặc $0.7$) và công thức tự rút gọn trơn tru về $G(r) = \frac{1}{|U|} \sum_{i \in U} g(i, r)$.

### 4.3. Đo mức phù hợp thời gian — $T(r)$ (`15%`, Thành phần 07)

Trong cơ sở dữ liệu, mỗi món ăn lưu `prep_minutes` và `cook_minutes` (số phút nguyên, đã bao gồm thời gian ướp/chờ/hầm bắt buộc theo [`ADR-009`](../07-decisions/ADR-009-cooking-and-waiting-time.md), bảo đảm `prep_minutes + cook_minutes > 0`) để giao diện hiển thị thân thiện, và quy đổi chính xác sang **đơn vị giờ** $t_r = \frac{\text{prep\_minutes} + \text{cook\_minutes}}{60.0} > 0$. Với thời gian mong muốn của người dùng $t^* > 0$ (**mặc định $t^* = 100.0\text{ giờ}$** nếu không nhập):

\[
T(r) = \min\!\left(1, \frac{t^*}{t_r}\right) \in (0, 1], \qquad t_r > 0
\]

- Khi người dùng không nhập thời gian ($t^* = 100.0\text{h}$), mọi món ăn thông thường ($t_r \le 100\text{h}$) đều đạt $T(r) = 1.0$ (không bị trừ điểm oan).
- Khi người dùng nhập thời gian mong muốn ngắn (ví dụ $t^* = 0.25\text{h}$ tức 15 phút), món nấu mất $t_r = 0.50\text{h}$ (30 phút) vẫn được giữ lại và nhận điểm tỷ lệ $T(r) = 0.25 / 0.50 = 0.50$.

### 4.4. Đo mức khớp sở thích — $P(r)$ (`10%`, Thành phần 07 & 08)

Gọi $F_u$ là tập nguyên liệu yêu thích của người dùng (`favorite_ingredient_ids`) và $\text{Ing}(r)$ là tập toàn bộ nguyên liệu có trong món ăn $r$:

\[
P(r) = \begin{cases}
0.5, & \text{nếu } |F_u| = 0 \text{ (quy ước trung lập khi người dùng chưa chọn nguyên liệu yêu thích)} \\[8pt]
\dfrac{|\text{Ing}(r) \cap F_u|}{|F_u|}, & \text{nếu } |F_u| > 0
\end{cases}
\]

### 4.5. Công thức tính điểm món ăn tổng hợp $S(r)$ & Giải thích tuyến tính XAI (Thành phần 14)

\[
\boxed{S(r) = 100 \times \big(0.50\,C(r, A) + 0.25\,G(r) + 0.15\,T(r) + 0.10\,P(r)\big) \in [0, 100]}
\]

Đóng góp điểm giải thích được (Score Breakdown XAI) của từng tiêu chí là tổ hợp tuyến tính chính xác (không hộp đen):

\[
\text{Contribution}_C = 50\,C, \quad \text{Contribution}_G = 25\,G, \quad \text{Contribution}_T = 15\,T, \quad \text{Contribution}_P = 10\,P, \qquad \sum_{k \in \{C,G,T,P\}} \text{Contribution}_k = S(r)
\]

**Quy tắc xếp hạng danh sách kết quả:**
1. Nhóm `availability = "ready"` (`READY`) luôn xếp trước nhóm `"missing"` (`UNKNOWN` / `MISSING_CONFIRMED`).
2. Trong từng nhóm, sắp xếp giảm dần theo `score DESC`, tiếp theo `len(missing_required_ingredient_ids) ASC`, `total_minutes ASC`, `recipe_id ASC`.

---

## 5. Ví dụ tính tay kiểm chứng xuyên suốt

### 5.1. Kịch bản 1 — Mặc định (Bỏ qua nguyên liệu chính, mặc định $t^* = 100\text{h}$, Guest $P = 0.5$)

Xét công thức **"Trứng xào cà chua"** (`prep_minutes = 5`, `cook_minutes = 10` $\implies t_r = 15\text{ phút} = 0.25\text{h}$):
- Nguyên liệu trong món: `Cà chua` (`core`, $w = 4$, `main` $\to g = 1.0$), `Trứng gà` (`core`, $w = 4$, `main` $\to g = 1.0$), `Dầu ăn` (`spice/pantry`, $w = 1$, `sub`), `Nước mắm` (`spice/pantry`, $w = 1$, `sub`), `Hành lá` (`optional`, ngoài $R_r$, `sub`). Tổng trọng số bắt buộc $\sum_{i \in R_r} w_{r,i} = 4 + 4 + 1 + 1 = 10$.
- **Trường hợp 1a — Đủ Cà chua, Trứng gà và gia vị bếp (`U = {Cà chua, Trứng gà}`, `X = []`, `F_u = []`):**
  - $C = \frac{4 + 4 + 1 + 1}{10} = 1.00 \implies \text{Contribution}_C = 50.00$
  - $G = \frac{1.0 + 1.0}{2} = 1.00 \implies \text{Contribution}_G = 25.00$
  - $T = \min(1, 100.0 / 0.25) = 1.00 \implies \text{Contribution}_T = 15.00$
  - $P = 0.50$ (trung lập) $\implies \text{Contribution}_P = 5.00$
  - **Tổng điểm:** $S = \mathbf{95.00}$, trạng thái `READY` (`availability = "ready"`). *(Nếu người dùng có $F_u = \{\text{Cà chua}, \text{Trứng gà}\}$ thì $P = 2/2 = 1.0 \implies S = \mathbf{100.00}$).*
- **Trường hợp 1b — Bếp hết Nước mắm (`X = [nuoc_mam_id]`):**
  - $C = \frac{4 + 4 + 1 + 0}{10} = 0.90 \implies \text{Contribution}_C = 45.00$, các tiêu chí $G=1.0, T=1.0, P=0.5$ giữ nguyên $\implies S = \mathbf{90.00}$, trạng thái `MISSING_CONFIRMED` (`availability = "missing"`, thiếu `Nước mắm`).
- **Trường hợp 1c — Chỉ quét 1 quả Cà chua (`U = {Cà chua}`, chưa rõ Trứng gà):**
  - $C = \frac{4 + 0 + 1 + 1}{10} = 0.60 \implies \text{Contribution}_C = 30.00$, $G = 1.00$, $T = 1.00$, $P = 0.50 \implies S = \mathbf{75.00}$, trạng thái `UNKNOWN` (`availability = "missing"`, cần kiểm tra `Trứng gà`).

### 5.2. Kịch bản 2 — Có chọn nguyên liệu chính (`0.7 / 0.3`), thời gian $t^* = 0.25\text{h}$ và nguyên liệu yêu thích

Xét công thức **"Đậu hũ sốt cà chua"** (`prep_minutes = 10`, `cook_minutes = 20` $\implies t_r = 30\text{ phút} = 0.50\text{h}$):
- Nguyên liệu bắt buộc $R_r$: `Đậu hũ` (`core`, $w = 4$, `main` $\to g = 1.0$), `Cà chua` (`secondary`, $w = 2$, `sub` $\to g = 0.5$), `Muối` ($w = 1$), `Dầu ăn` ($w = 1$) $\implies$ tổng trọng số $= 8$.
- Người dùng có `U = {Đậu hũ, Cà chua}` (đủ gia vị), chọn **Đậu hũ làm nguyên liệu chính** (`U_main = {Đậu hũ}` $\to w = 0.7$, `U_sub = {Cà chua}` $\to w = 0.3$), đặt thời gian mong muốn $t^* = 0.25\text{h}$, và có danh sách yêu thích `F_u = {Đậu hũ, Thịt ba chỉ}`:
  - $C = 8/8 = 1.00 \implies \text{Contribution}_C = 50.00$
  - $G = \frac{0.7 \times 1.0 + 0.3 \times 0.5}{0.7 + 0.3} = 0.85 \implies \text{Contribution}_G = 21.25$
  - $T = \min(1, 0.25 / 0.50) = 0.50 \implies \text{Contribution}_T = 7.50$
  - $P = 1 / 2 = 0.50 \implies \text{Contribution}_P = 5.00$
  - **Tổng điểm:** $S = 50.00 + 21.25 + 7.50 + 5.00 = \mathbf{83.75}$ (`READY`).

---

## 6. Đa dạng hóa MMR (Thành phần 09) & Mở rộng Học máy Cá nhân hóa (Thành phần 08)

1. **Đa dạng hóa Top-K bằng MMR (`TP 09`):** Sau khi tính điểm chuẩn $S(r)$, thuật toán Maximal Marginal Relevance tái sắp xếp trong từng bậc khả thi theo $\text{MMR}(r) = \lambda_{\text{mmr}}\frac{S(r)}{100} - (1 - \lambda_{\text{mmr}})\max_{s \in D}\text{Sim}(r, s)$ ($\lambda_{\text{mmr}} = 0.7$) để tránh trả về liên tiếp nhiều biến thể trùng phương pháp nấu. **Bất biến an toàn:** MMR tuyệt đối không bao giờ khôi phục các món đã bị `BLOCKED` do dị ứng.
2. **Học tăng cường từ phản hồi lịch sử (`TP 08` — Tùy chọn Giai đoạn 4–5):** Bên cạnh điểm sở thích nguyên liệu tường minh $P(r)$, với người dùng có đủ lịch sử đánh giá (`recommendation_feedback`, lấy bản ghi `updated_at` mới nhất trên mỗi cặp `(user_id, recipe_id)` theo [`ADR-012`](../07-decisions/ADR-012-feedback-uniqueness-and-context.md)), hệ thống hỗ trợ kết hợp xác suất Logistic Regression $p_{u,r} = \sigma(\theta_u^T x_r)$ qua công thức trộn cold-start $S_{\text{final}}(u, r) = (1 - \lambda_{\text{pers}})S(r) + 100\,\lambda_{\text{pers}}p_{u,r}$ (mặc định $\lambda_{\text{pers}} = 0$ cho `Guest` và `User` mới) để phục vụ thực nghiệm đối chứng **4 phiên bản `A – B (Tversky) – C (3-State + MCDA C,G,T,P + MMR) – D (C + LR)`** bằng `Precision@5` và `nDCG@5` ở Thành phần 12.

---

## 7. Thực nghiệm Đối chứng 4 Biến thể (`A – B – C – D`) & Hiệu năng `PERF-02` (Giai đoạn 5 — `AI-04`, `DEF-07`)

### 7.1. Thiết lập thực nghiệm tái lập (`Reproducible Setup`)

- **Tập kịch bản kiểm chứng:** $N = 120$ kịch bản độc lập (`>= 100` theo `AI-04` / `DEF-07`), sinh tất định với `seed = 20261115` trên danh mục chuẩn 24 công thức đa dạng vùng miền (`VN`, `EU`, `US`) và phương pháp chế biến (`stir_fry`, `pan_fry`, `boil`, `braise`, `bake`), trải đều trên 4 nhóm hồ sơ người dùng (`UserPersona`) có dị ứng (`egg`, `soy`), quỹ thời gian và gu ẩm thực khác nhau.
- **Chia tách theo thời gian nghiêm ngặt (`Temporal Split` cho Biến thể `D`):** Toàn bộ mẫu huấn luyện `recommendation_feedback` của từng người dùng nằm trong khoảng $[T_0 - 14\text{ ngày}, T_0 - 1\text{ ngày}]$ (chỉ đánh giá tập công thức chỉ số chẵn), trong khi 120 kịch bản đánh giá diễn ra tại $t_{\text{eval}} \ge T_0$ trên toàn bộ danh mục (50% công thức chưa từng xuất hiện trong lịch sử phản hồi), đảm bảo mô hình Logistic Regression (`10` đặc trưng giải thích được, $\lambda_{\text{pers,max}} = 0.12$ áp dụng khi $C(r, A) \ge 0.60$) tổng quát hóa theo đặc trưng thay vì học vẹt ID món.
- **Thang điểm phù hợp khách quan (`rel` $\in \{0, 1, 2, 3\}$):** Gán trước khi chạy bất kỳ bộ xếp hạng nào; mọi công thức vi phạm ràng buộc cứng (dị ứng, vượt `max_total_minutes`, lệch `cuisine_codes`) hoặc $C(r, A) < 0.50$ bắt buộc nhận `rel = 0`.
- **Lệnh tái lập một bước từ thư mục gốc `foodVision AI`:**
  ```bash
  python backend/scripts/run_ranker_ablation.py
  ```

### 7.2. Bảng kết quả đối chứng thực nghiệm (`Top-K = 5`, `N = 120`, `seed = 20261115`)

| Biến thể | Mô tả cấu hình thuật toán | `Precision@5` ($\uparrow$) | `nDCG@5` ($\uparrow$) | `CVR@5` ($\downarrow$) | `ILD@5` ($\uparrow$) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`A`** | Đếm giao nguyên liệu đồng nhất (không trọng số vai trò, không lọc cứng `TP 04`, không MMR) | `0.5200` | `0.6462` | `18.67%` | `0.7246` |
| **`B`** | Tương đồng tập bất đối xứng Tversky ($\alpha = 0.3, \beta = 2.0$ — cơ sở `TP 06`) | `0.6450` | `0.7664` | `18.67%` | `0.6802` |
| **`C`** | Suy diễn 3 trạng thái (`TP 04`) + Trọng số `4-2-1-0` + MCDA `(C, G, T, P)` + MMR (`TP 09`) | **`0.7817`** | `0.9162` | **`0.00%`** | `0.7066` |
| **`D`** | Biến thể `C` + Học sở thích Logistic Regression (`TP 08`, `Temporal Split`, $\lambda_{\text{pers}} \le 0.12$) | `0.7750` | **`0.9417`** | **`0.00%`** | **`0.7149`** |

**Nhận xét học thuật từ số liệu thực nghiệm:**
1. **Hiệu quả phạt bất đối xứng (`A` $\to$ `B`):** Tversky ($\beta = 2.0 > \alpha = 0.3$) phạt nặng nguyên liệu bắt buộc bị thiếu thay vì cộng dồn gia vị phổ thông, nâng `Precision@5` từ `0.5200` lên `0.6450` (`+24.0%`) và `nDCG@5` từ `0.6462` lên `0.7664` (`+18.6%`). Tuy nhiên, nếu thiếu tầng suy diễn ràng buộc cứng `TP 04`, cả `A` và `B` đều để lọt `18.67%` kết quả vi phạm dị ứng/thời gian (`CVR@5`).
2. **Đột phá an toàn & chất lượng của kiến trúc lai tri thức (`B` $\to$ `C`):** Tích hợp cổng suy diễn thế giới mở 3 trạng thái (`READY` / `UNKNOWN` / `MISSING_CONFIRMED` / `BLOCKED`), trọng số vai trò `4-2-1-0`, hàm mục tiêu tuyến tính `S = 100*(0.50C + 0.25G + 0.15T + 0.10P)` và tái xếp hạng đa dạng hóa MMR giúp triệt tiêu hoàn toàn vi phạm ràng buộc cứng (**`CVR@5 = 0.00%`**), đẩy `Precision@5` lên **`0.7817`** (`+50.3%` so với `A`) và khôi phục độ đa dạng nội danh sách `ILD@5` từ `0.6802` lên `0.7066`.
3. **Giá trị gia tăng của cá nhân hóa học máy có kiểm soát (`C` $\to$ `D`):** Khi người dùng có lịch sử đánh giá ($\ge 3$ mẫu hợp lệ sau khử trùng lặp `ADR-012`), Logistic Regression đẩy các công thức khớp gu ẩm thực & phương pháp chế biến (`rel = 3`) lên đầu Top-5, nâng **`nDCG@5` đạt đỉnh `0.9417`** (`+0.0255` so với `C`) và **`ILD@5 = 0.7149`**, đồng thời bảo toàn tuyệt đối `CVR@5 = 0.00%`.

### 7.3. Kết quả kiểm thử hiệu năng `PERF-02` (`520` công thức `published`, `40` truy vấn liên tiếp)

Thực thi trên môi trường `Python 3.11.7` (`Windows 10`, kho `520` công thức `published` $\ge 500$ theo `NFR-02`):

| Endpoint kiểm thử | Quy mô kho món | `mean` (`ms`) | `p50` (`ms`) | `p95` (`ms`) | Ngưỡng mục tiêu `p95` (`PERF-02`) | Kết luận |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `POST /api/v1/recommendations` (`diversify=true`) | `520` | `25.35` | `22.58` | **`42.99`** | `<= 1000.0 ms` | **ĐẠT** (nhanh hơn ngưỡng 23 lần) |
| `GET /api/v1/recipes?q=...&limit=20` | `520` | `7.49` | `6.90` | **`10.21`** | `<= 500.0 ms` | **ĐẠT** (nhanh hơn ngưỡng 48 lần) |

