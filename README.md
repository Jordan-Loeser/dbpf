# dbpf.py

A tool for parsing DBPF (aka .package) files, a format that is described in more detail [here](https://modthesims.info/wiki.php?title=DBPF).

## Classes

`DBPF(fd)`:
	Takes a file object and parses its header, index, and record entries into accessible properties.

`TGI(tid, gid, iid)`: Takes a Target, Group, and Instance ID and parses it into a printable TGI object.


## Named Tuples

Name | Values
--- | ---
Header | `fileIdentifier`,`fileMajor`,`fileMinor`,`userMajor`,`userMinor`,`flags`,`creationTime`,`updatedTime`,`indexRecordMajorVersion`,`indexRecordEntryCount`,`indexOffsetBytesV1`,`indexRecordSizeBytes`,`holeIndexEntryCount`,`holeIndexOffset`,`holeIndexSize`,`indexMinorVersion`,`indexOffsetBytes`,`reserved`
Index | `version`,`count`,`offset`,`size`
IndexEntry | `mType`,`mGroup`,`mInstanceEx`,`mInstance`,`mnPosition`,`mnSize`,`mnSizeDecompressed`,`mnCompressionType`,`mnCommitted`
Record | `key`,`offset`,`length`,`raw`

## Usage

Print a list of Record objects with accessible propoerties.

```python
db = DBPF(fd_input, verbose=True)
for record in db.records:
    print(record.key)
    print(record.raw)

```