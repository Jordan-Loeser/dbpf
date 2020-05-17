#!/usr/bin/env python3
import struct
import os.path
from collections import namedtuple

# Based off the guidelines provided here:
# http://simswiki.info/DatabasePackedFile
# https://forums.thesims.com/en_US/discussion/779844/maxis-documentation
# http://simswiki.info/images/e/e8/DBPF_File_Format_v1.1.png
# http://simswiki.info/images/e/e8/DBPF_File_Format_v2.0.png
headerTemplate = {
	'byteOrder': '<',
    'fileIdentifier': '4s',				# 0
	'fileMajor': 'I',					# 1
	'fileMinor': 'I',					# 2
	'userMajor': 'I',					# 3
	'userMinor': 'I',					# 4
	'flags': 'I',						# 5			# unused
	'creationTime': 'I',				# 6
	'updatedTime': 'I',					# 7
	'indexRecordMajorVersion': 'I',		# 8
	'indexRecordEntryCount': 'I',		# 9
	'indexOffsetBytesV1': 'I',			# 10		# deprecated
	'indexRecordSizeBytes': 'I',		# 11
	'holeIndexEntryCount': 'I',			# 12
	'holeIndexOffset': 'I',				# 13
	'holeIndexSize': 'I',				# 14
	'indexMinorVersion': 'I',			# 15
	'indexOffsetBytes': 'Q',			# 16
	'reserved': '24s',					# 17
}

indexEntryTemplate = {
	'byteOrder': '<',
    'mType': 'I',						# 0
	'mGroup': 'I',						# 1
	'mInstanceEx': 'I',					# 2
	'mInstance': 'I',					# 3
	'mnPosition': 'I',					# 4
	'mnSize': 'I',						# 5
	'mnSizeDecompressed': 'I',			# 6
	'mnCompressionType': 'H',			# 7
	'mnCommitted': 'H',  				# 8
}

class Header(namedtuple("DBPF_Header", ' '.join(list(headerTemplate.keys())[1:]))): pass
class Index(namedtuple("DBPF_Index", 'version count offset size')): pass
class IndexEntry(namedtuple("DBPF_IndexEntry", ' '.join(list(indexEntryTemplate.keys())[1:]))): pass
class Record(namedtuple("DBPF_Record", 'tgi offset length raw')): pass

# Build struct for parsing
headerTemplateString = ''.join(headerTemplate.values())
HeaderStruct = struct.Struct(headerTemplateString)

# Configure the Index Entry template
indexEntryTemplateString = ''.join(indexEntryTemplate.values())
IndexEntryStruct = struct.Struct(indexEntryTemplateString)

class DBPF:
	"""a database backed DBPF file"""
	def __init__(self, fd, verbose=False):
		self._fd = fd
		self.verbose = verbose

		# Read and parse the header
		fd.seek(0)
		headerData = HeaderStruct.unpack(fd.read(HeaderStruct.size))
		self.header = Header(*headerData)

		# Validate header
		if self.header[0] != b'DBPF':
			raise DBPFException('Not a DBPF file')

	## HEADER INFORMATION

	@property
	def version(self):
		"""a real number representing the header version"""
		hdr = self.header
		return version(hdr.fileMajor, hdr.fileMinor)

	@property
	def user_version(self):
		"""a real number representing the user version"""
		hdr = self.header
		return version(hdr.userMajor, hdr.userMinor)

	@property
	def flags(self):
		"""flags"""
		return self.header.flags

	@property
	def ctime(self):
		"""creation time"""
		return self.header.creationTime

	@property
	def mtime(self):
		"""modification time"""
		return self.header.updatedTime

	@property
	def index(self):
		"""the table of files in this DBPF"""
		hdr = self.header
		offset = hdr.indexOffsetBytesV1 if hdr.fileMajor == 1 else hdr.indexOffsetBytes
		return Index(
			version(hdr.indexRecordMajorVersion, hdr.indexMinorVersion),	# version
			hdr.indexRecordEntryCount,										# count
			offset + 4,														# offset (ignore 4 flag bytes)
			hdr.indexRecordSizeBytes - 4,									# size	 (^^^				 )
		)

	@property
	def holes(self):
		"""the table of holes in this DBPF"""
		hdr = self.header
		return Index(0, hdr.holeIndexEntryCount, hdr.holeIndexOffset, hdr.holeIndexSize)

	## PARSING HELPERS

	@property
	def _index_width(self):
		"""the width of records in the index table"""
		# It is not clear how wide this should be depending on the version...
		# This is definitely optimized for version 2.0
		idx = self.index
		width = int(idx.size / idx.count)
		if (self.verbose): print('[*] _index_width(): width={0}'.format(width))
		return width

	def _index_entries(self):
		"""parse the passed """
		index_entries = []

		# Parse from Index
		ind = self.index
		offset = ind.offset
		length = ind.size
		width = self._index_width

		if (self.verbose): print('[*] _index_entries(): offset={0}, length={1}, width={2}'.format(offset, length, width))

		# Read and parse the index entries
		self._fd.seek(offset)
		for i in range(0, length, width):
			indexEntryData = IndexEntryStruct.unpack(self._fd.read(width))
			newIndexEntry = IndexEntry(*indexEntryData)
			index_entries.append(newIndexEntry)
		return index_entries

	@property
	def records(self):
		"""retrieve all TGIs"""
		records = []
		for idx_entry in self._index_entries():
			mnSize = idx_entry.mnSizeDecompressed
			mnPosition = idx_entry.mnPosition

			self._fd.seek(mnPosition)
			newRecord = Record(
				raw=self._fd.read(mnSize),
				tgi=tgi.TGI(idx_entry.mType, idx_entry.mGroup, idx_entry.mInstance),
				offset=mnPosition,
				length=mnSize,
			)
			records.append(newRecord)
		return records

	# TODO: implement function that can generate .package from list of filepaths

# util
def version(major, minor): return float('.'.join([str(major),str(minor)]))

#exceptions
class ArgumentException(Exception): pass
class DBPFException(Exception): pass

if __name__ == "__main__":
	import sys
	import tgi

	filename_input = sys.argv[1]
	if not os.path.exists(filename_input):
		raise ArgumentException('File')
	with open(filename_input, 'rb') as fd_input:
		db = DBPF(fd_input, verbose=True)
		print('[*] db.ecords:', db.records)