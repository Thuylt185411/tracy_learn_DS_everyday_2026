Vì evidently chỉ **monitor current và ref,**

Nhưng em thì quan tâm cả **timeseries phân phối từng tháng** nữa

# Các nhóm metrics

## A. Data quality

Giám sát theo feature

* **Missing rate** theo từng biến / theo segment
* **Out-of-range / invalid** (vd: tuổi < 18, income âm, ngày sai format, category lạ)
* **Duplicate key / row explosion** (trùng application_id, customer_id…)

**Ngưỡng tham khảo (tùy dữ liệu mà chỉnh):**

* Missing rate tăng **+2–5 điểm %** so với baseline: cảnh báo;  **>+5–10 điểm %** : nghiêm trọng
* Tỷ lệ invalid/out-of-range: **>0.5–1%** (cảnh báo), **>1–2%** (nghiêm trọng)

## B. Drift / Stability

| **Concept Drift**                                           | **Data Drift**                                                              | **Covariate Shift**                                       |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| * Mối quan hệ giữa**features và target**thay đổi* P(Y | X) thay đổi* Data distribution drift can be a symptom of**concept drift** | * Phân phối của**features**thay đổi* P(X) thay đổi |
|                                                                   |                                                                                   |                                                                 |

**Chỉ số phổ biến:**

* **PSI (Population Stability Index)** cho feature, score, PD band
* KS test / Wasserstein… (có thể dùng, nhưng PSI là chuẩn “dễ vận hành”)

**Ngưỡng PSI thường dùng:**

* **PSI < 0.10** : ổn
* **0.10 – 0.25** : drift vừa (cần soi theo segment + nguyên nhân)
* **> 0.25** : drift mạnh (đỏ)

## C. Discrimination

Đo khả năng xếp hạng rủi ro:

* **AUC-ROC** (hoặc  **Gini = 2*AUC − 1** )
* **KS**
* Với dữ liệu lệch lớp mạnh:  **PR-AUC** ,  **Recall@TopX%** , **Bad rate in deciles**

**Ngưỡng tham khảo (giám sát theo “tụt so với baseline”, không chỉ giá trị tuyệt đối):**

* AUC giảm  **>0.02–0.03** : cảnh báo;  **>0.05** : nghiêm trọng
* KS giảm  **>3–5 điểm %** : cảnh báo;  **>5–10 điểm %** : nghiêm trọng
* Lift/Bad rate ở nhóm top-risk bị “lỏng” rõ rệt: cảnh báo mạnh

## Bảng ngưỡng tham khảo

| Nhóm          | Metric              | Xanh     | Vàng                   | Đỏ            |
| -------------- | ------------------- | -------- | ----------------------- | --------------- |
| Drift          | PSI (feature/score) | <0.10    | 0.10–0.25              | >0.25           |
| Discrimination | ΔAUC vs baseline   | ≥ -0.02 | -0.02 đến -0.05       | < -0.05         |
| Discrimination | ΔKS vs baseline    | ≥ -3pp  | -3 đến -5pp           | < -5pp          |
| Data quality   | Missing rate tăng  | < +2pp   | +2 đến +5pp           | > +5pp          |
| Calibration    | E/O                 | 0.9–1.1 | 0.8–0.9 hoặc 1.1–1.2 | <0.8 hoặc >1.2 |
| Strategy       | Override rate tăng | < +3pp   | +3 đến +7pp           | > +7pp          |

# Phương pháp phát hiện DRIFT

## 1. Statistical Tests

[Customize Data Drift - Evidently AI - Documentation](https://docs.evidentlyai.com/metrics/customize_data_drift)

### 1.1. Population Stability Index (PSI)

Population Stability Index được coi là chỉ số ổn định tổng thể là một phép đo được sử dụng để đo phân phối của sự thay đổi dữ liệu giữa hai tập dữ liệu.

PSI áp dụng cho feature, score và PD band.

* Đo lường sự khác biệt giữa hai distributions
* PSI = Σ (Actual% - Expected%) * ln(Actual% / Expected%)
* Thang đánh giá:
  * PSI < 0.1: Không có drift đáng kể
  * 0.1 < PSI < 0.2: Drift nhẹ
  * PSI > 0.2: Drift đáng kể

### 1.2. Characteristic Stability Index (CSI)

* Đo lường sự thay đổi trong mean và standard deviation
* CSI = |μ_new - μ_base|/σ_base + |σ_new - σ_base|/σ_base
* Nhạy với thay đổi trong shape của distribution

### 1.3. Kolmogorov-Smirnov test

* So sánh cumulative distributions
* Không có giả định về distribution
* Nhạy với mọi loại khác biệt trong distribution

### 1.4. Chi-square test

* So sánh frequencies trong các bins
* Phù hợp với categorical data
* Yêu cầu đủ số lượng samples trong mỗi bin

### 1.5. Kullback-Leibler (KL) Divergence

* Đo lường information loss giữa hai distributions
* KL(P||Q) = Σ P(x) * log(P(x)/Q(x))
* Các biến thể:
  * Symmetric KL: (KL(P||Q) + KL(Q||P)) / 2
  * Relative Entropy Ratio: KL(P||Q) / (H(P) + H(Q))
* Ưu điểm:
  * Nhạy với subtle changes trong distribution
  * Có cơ sở information theory
* Nhược điểm:
  * Không symmetric trong dạng cơ bản
  * Yêu cầu đủ data để ước lượng distributions

### 1.6. Jensen-Shannon Divergence (JSD)

* Cải tiến symmetric của KL divergence
* JSD(P||Q) = 0.5 * (KL(P||M) + KL(Q||M)), where M = (P+Q)/2
* Giá trị từ 0 (giống nhau) đến 1 (hoàn toàn khác)
* Ưu điểm:
  * Luôn symmetric
  * Bounded between [0,1]
  * Smooth và stable

### 1.7. Wasserstein Distance

* Earth Mover's Distance
* Đo lường cost để transform một distribution thành distribution khác
* Ưu điểm:
  * Robust với outliers
  * Có ý nghĩa hình học
  * Hoạt động tốt với non-overlapping distributions

## Machine Learning Methods

#### Adversarial Validation

* Train binary classifier để phân biệt train/test data
* AUC score cao => có drift
* Ưu điểm:
  * Có thể phát hiện complex patterns
  * Tự động feature selection
* Nhược điểm:
  * Yêu cầu đủ data để train
  * Có thể overfitting với small samples

#### Domain Classifier

* Tương tự adversarial validation
* Sử dụng deep learning cho high-dimensional data
* Thích hợp cho image/text data

#### Unsupervised Methods

* **PCA-based Detection** : Phát hiện drift thông qua thay đổi trong principal components
* **Autoencoder** : Sử dụng reconstruction error để phát hiện anomalies và drift

### Performance Monitoring

* **Model Performance Monitor** : Theo dõi hiệu suất mô hình theo thời gian
* Metrics tracking (accuracy, AUC, F1, RMSE)
* Feature importance drift detection
* Prediction pattern analysis
* Comprehensive reporting

### Lựa chọn phương pháp phát hiện

1. Categorical Features: **Chi-square test, PSI, KL Divergence**
2. Numerical Features:  **KS test, Wasserstein Distance, CSI, JSD, PSI** (sau khi chia bins)
3. High-dimensional Data: **Adversarial Validation; Domain Classifier**
4. Time Series Data: **Sliding window với statistical tests; Sequential drift detection**

## Khác

Tabular data

The following methods apply to **tabular **data: numerical or categorical columns in data definition.

| **StatTest**                                   | **Applicable to**                                                                                    | **Drift score**                                                                                  |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **ks**``Kolmogorov–Smirnov (K-S) test         | tabular data``only numerical**Default method for numerical data, if ≤ 1000 objects**                | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **chisquare**``Chi-Square test                 | tabular data``only categorical**Default method for categorical with > 2 labels, if ≤ 1000 objects** | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **z**``Z-test                                  | tabular data``only categorical**Default method for binary data, if ≤ 1000 objects**                 | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **wasserstein**``Wasserstein distance (normed) | tabular data``only numerical**Default method for numerical data, if > 1000 objects**                 | returns**distance** ``drift detected when**distance**≥**threshold**``default threshold: 0.1     |
| **kl_div**``Kullback-Leibler divergence        | tabular data``numerical and categorical                                                                    | returns**divergence** ``drift detected when**divergence**≥**threshold**``default threshold: 0.1 |
| **psi**``Population Stability Index (PSI)      | tabular data``numerical and categorical                                                                    | returns**psi_value** ``drift detected when**psi_value**≥**threshold**``default threshold: 0.1   |
| **jensenshannon**``Jensen-Shannon distance     | tabular data``numerical and categorical**Default method for categorical, if > 1000 objects**         | returns**distance** ``drift detected when**distance**≥**threshold**``default threshold: 0.1     |
| **anderson**``Anderson-Darling test            | tabular data``only numerical                                                                               | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **fisher_exact**``Fisher’s Exact test         | tabular data``only categorical                                                                             | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **cramer_von_mises**``Cramer-Von-Mises test    | tabular data``only numerical                                                                               | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **g-test**``G-test                             | tabular data``only categorical                                                                             | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **hellinger**``Hellinger Distance (normed)     | tabular data``numerical and categorical                                                                    | returns**distance** ``drift detected when**distance**>=**threshold**``default threshold: 0.1     |
| **mannw**``Mann-Whitney U-rank test            | tabular data``only numerical                                                                               | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **ed**``Energy distance                        | tabular data``only numerical                                                                               | returns**distance** ``drift detected when**distance >= threshold**``default threshold: 0.1       |
| **es**``Epps-Singleton test                    | tabular data``only numerical                                                                               | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **t_test**``T-Test                             | tabular data``only numerical                                                                               | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **empirical_mmd**``Empirical-MMD               | tabular data``only numerical                                                                               | returns**p_value** ``drift detected when**p_value < threshold**``default threshold: 0.05         |
| **TVD**``Total-Variation-Distance              | tabular data``only categorical                                                                             | returns**p_value** ``drift detected when**p_value**<**threshold**``default threshold: 0.05       |
