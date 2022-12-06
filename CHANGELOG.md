### [0.3.7](https://github.com/vzhd1701/csv2notion/compare/v0.3.6...v0.3.7) (2022-12-06)

### Bug Fixes

- improve URL permission check ([c74b759](https://github.com/vzhd1701/csv2notion/commit/c74b759b895100bd6c62362eee22895ddf6b1cdc))
- update notion SDK ([94d5d60](https://github.com/vzhd1701/csv2notion/commit/94d5d60782b5ea6b939a4b2c79d0353448595c3f))

### [0.3.6](https://github.com/vzhd1701/csv2notion/compare/v0.3.5...v0.3.6) (2022-11-14)

### Bug Fixes

- add support for date ranges ([ee3ebbd](https://github.com/vzhd1701/csv2notion/commit/ee3ebbd9638f9734e6f5644eb60eeabaf5be36ea))
- add support for inline databases ([6eded8b](https://github.com/vzhd1701/csv2notion/commit/6eded8b332f37d4b99d1274f2261a9078cdd09de)), closes [#12](https://github.com/vzhd1701/csv2notion/issues/12)
- show error if no edit permissions ([348e060](https://github.com/vzhd1701/csv2notion/commit/348e060007acbe083fb158e0d5f766a1651c58d0))

### [0.3.5](https://github.com/vzhd1701/csv2notion/compare/v0.3.4...v0.3.5) (2022-08-30)

### Features

- add support for status columns ([4477843](https://github.com/vzhd1701/csv2notion/commit/447784318a770acf8eba48d3b7df46687b18b988))

### [0.3.4](https://github.com/vzhd1701/csv2notion/compare/v0.3.3...v0.3.4) (2022-08-01)

### Bug Fixes

- update notion SDK to avoid rate limit errors ([129fed4](https://github.com/vzhd1701/csv2notion/commit/129fed4d508e8768e0a1008ba41c4b01b4bfacf3))

### [0.3.3](https://github.com/vzhd1701/csv2notion/compare/v0.3.2...v0.3.3) (2022-07-21)

### Bug Fixes

- fix emoji icon parsing ([01f613e](https://github.com/vzhd1701/csv2notion/commit/01f613ef308ad49bf72befe88787fa3bad741997))

### [0.3.2](https://github.com/vzhd1701/csv2notion/compare/v0.3.1...v0.3.2) (2022-07-20)

### Bug Fixes

- clarify warning message for unsettable column types ([bcb34e2](https://github.com/vzhd1701/csv2notion/commit/bcb34e2350b5ee33b416bcc8dfddd2758277e160))

### [0.3.1](https://github.com/vzhd1701/csv2notion/compare/v0.3.0...v0.3.1) (2022-07-13)

### Bug Fixes

- show which columns are duplicate in warning ([414d4a9](https://github.com/vzhd1701/csv2notion/commit/414d4a90372775df99fbaa0ffe86369677bd1135))
- truncate excess columns if column number is inconsistent ([9ef7a37](https://github.com/vzhd1701/csv2notion/commit/9ef7a3731f700812f5ca03a36a18792ca48cf1f7)), closes [#5](https://github.com/vzhd1701/csv2notion/issues/5)

## [0.3.0](https://github.com/vzhd1701/csv2notion/compare/v0.2.1...v0.3.0) (2022-07-09)

### Features

- add --randomize-select-colors flag ([27cb75b](https://github.com/vzhd1701/csv2notion/commit/27cb75b25184a64d1c653f6bd25b920ef28ac8de))

### [0.2.1](https://github.com/vzhd1701/csv2notion/compare/v0.2.0...v0.2.1) (2022-06-04)

### Bug Fixes

- update notion-vzhd1701-fork to avoid network error on file upload ([ebb1b49](https://github.com/vzhd1701/csv2notion/commit/ebb1b49b6be7d8646406b5e21ebec50781f73907))

## [0.2.0](https://github.com/vzhd1701/csv2notion/compare/v0.1.3...v0.2.0) (2022-05-24)

### Features

- add --fail-on-unsupported-columns flag ([846b4fd](https://github.com/vzhd1701/csv2notion/commit/846b4fd2ba7bee6801bfe4da75c99a003f5f662f))
- add --merge-skip-new flag ([3d7b805](https://github.com/vzhd1701/csv2notion/commit/3d7b805385818a4a157064184f061f65af87a302))

### Bug Fixes

- add more warnings ([2777cfe](https://github.com/vzhd1701/csv2notion/commit/2777cfe17300519ca803c5b7cb35303162a68e5d))
- add support for created/updated time column types ([6fbb3bc](https://github.com/vzhd1701/csv2notion/commit/6fbb3bcb7a32736ee08b0c64f0d661d68dd75217))
- add support for file column type ([4cf2b5a](https://github.com/vzhd1701/csv2notion/commit/4cf2b5a86958a22510ffcff37797c4211e2a826b))
- add support for notion URLs in relations ([0c3a6e6](https://github.com/vzhd1701/csv2notion/commit/0c3a6e608bebd1875bf797ecb1b8809d56f54aa2))
- add support for person column type ([e897c2d](https://github.com/vzhd1701/csv2notion/commit/e897c2d3189c503e6d33e6d05d038d1eb130c1a9))
- change --missing-relations-action into --add-missing-relations ([16f284f](https://github.com/vzhd1701/csv2notion/commit/16f284fd7084ddfe5f2bd1acae21bdaff4bea1ae))
- fail if no columns left after validation ([01e9cd9](https://github.com/vzhd1701/csv2notion/commit/01e9cd9cef6306a0fa3b643afad4988a3d7471e1))
- get existing row only during merge ([22d2b09](https://github.com/vzhd1701/csv2notion/commit/22d2b094343a394cf0b149e79ac05e1aae078422))
- make only last timestamp column count ([2aca947](https://github.com/vzhd1701/csv2notion/commit/2aca9477fcff5c29f4082ea9f8ae4d62bb4a02c2))
- rename --custom-types into --column-types ([de142b7](https://github.com/vzhd1701/csv2notion/commit/de142b797029c529cb43e83af52bea068d1c3c26))
- rename --fail-on-unsupported-columns into --fail-on-unsettable-columns ([f60e747](https://github.com/vzhd1701/csv2notion/commit/f60e747b449fd09cc7103ce94f6e3bb6d5f0aa35))
- split --help options into groups ([a051eb4](https://github.com/vzhd1701/csv2notion/commit/a051eb48ce2140c15131aab232bdc32a70b8b6c3))
- split --missing-columns-action into --add-missing-columns and --fail-on-missing-columns ([804908d](https://github.com/vzhd1701/csv2notion/commit/804908d238fdbc51d04c4af9fcda1e6ff2fb11da))

### [0.1.3](https://github.com/vzhd1701/csv2notion/compare/v0.1.2...v0.1.3) (2022-05-09)

### Bug Fixes

- avoid 100 rows limit when retrieving all rows from DB ([24244f7](https://github.com/vzhd1701/csv2notion/commit/24244f7f1ea846f8ad810565b152249e6944b51c))

### [0.1.2](https://github.com/vzhd1701/csv2notion/compare/v0.1.1...v0.1.2) (2022-05-08)

### Features

- add --image-caption-column option ([6e39128](https://github.com/vzhd1701/csv2notion/commit/6e39128ed44afab581d39698913f87ddec21278a))
- add --verbose option ([5fcb118](https://github.com/vzhd1701/csv2notion/commit/5fcb118e2238b44c549c627d07ceda34b8a8158d))

### Bug Fixes

- add better thread isolation ([69305a5](https://github.com/vzhd1701/csv2notion/commit/69305a54323dfb9f2458b064802ab985ee3b69b4))
- add support for csv with utf-8 BOM encoding ([ed97acb](https://github.com/vzhd1701/csv2notion/commit/ed97acbc763137d13a8f4dff040173d5b96a7898))
- avoid reuploading unmodified images ([198829e](https://github.com/vzhd1701/csv2notion/commit/198829ebfb56f7fc03c0be618c23a24b8281960e))
- handle file_ids properly on merge with images ([8865433](https://github.com/vzhd1701/csv2notion/commit/886543345ed0347eb4756da57e744be669a86b5a))
- make it easier to abort ongoing operation ([830dc92](https://github.com/vzhd1701/csv2notion/commit/830dc922fae0590e630053ea19b1c5c4cfaa90b8))
- prevent adding icon and image columns to new db ([989a09a](https://github.com/vzhd1701/csv2notion/commit/989a09a3b48332c6479b448f8067da03ac41516d))

### [0.1.1](https://github.com/vzhd1701/csv2notion/compare/v0.1.0...v0.1.1) (2022-05-05)

### Features

- add --default-icon option ([ef8be2d](https://github.com/vzhd1701/csv2notion/commit/ef8be2dbf6e0fb1672a417720819bf50dee93e01))
- add --fail-on-inaccessible-relations option ([781cda4](https://github.com/vzhd1701/csv2notion/commit/781cda4630ab73350c33ce9673932ad90fb19171))

### Bug Fixes

- guess empty columns type as text ([27a257d](https://github.com/vzhd1701/csv2notion/commit/27a257d49ef46890f3a4e0af361ac64cbd525eea))
- make new DB columns follow same order as CSV ([1158464](https://github.com/vzhd1701/csv2notion/commit/1158464bc238717c45cef36371bad41f931805a6))

## 0.1.0 (2022-05-04)
