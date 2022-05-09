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
