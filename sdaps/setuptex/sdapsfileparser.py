# -*- coding: utf8 -*-
# SDAPS - Scripts for data acquisition with paper based surveys
# Copyright (C) 2008, Christoph Simon <christoph.simon@gmx.eu>
# Copyright (C) 2008, Benjamin Berg <benjamin@sipsolutions.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import xml.sax
import zipfile
import re
from latexmap import mapping

from sdaps import model

QOBJECT_PREFIX = u'QObject'
ANSWER_PREFIX  = u'Answer'
BOX  = u'Box'

index_re = re.compile(r'''^(?P<index>(?:[0-9]+\.)+) (?P<string>.*)$''')
def get_index_and_string(string):
	match = index_re.match(string)
	if match is None:
		return None, string

	string = match.group('string')
	index = match.group('index')
	index = index.split('.')[:-1]
	index = tuple([int(x) for x in index])

	return index, string


re_mapping = {}
for token, replacement in mapping.iteritems():
	regexp = re.compile(u'%s(?=^w|})' % re.escape(token))
	re_mapping[regexp] = replacement


def latex_to_unicode(string):
	string = unicode(string)
	for regexp, replacement in re_mapping.iteritems():
		string, count = regexp.subn(replacement, string)

	def ret_char(match):
		return match.group('char')
	string, count = re.subn(r'\\IeC {(?P<char>.*?)}', ret_char, string)
	return string

def parse (survey, boxes) :

	sdaps_file = open(survey.path('questionnaire.sdaps'))
	# the file is encoded in ascii format
	sdaps_data = sdaps_file.read().decode('ascii')
	qobject = None
	auto_numbering_id = (0,)

	for line in sdaps_data.split('\n'):
		line = line.strip()
		if line == "":
			continue
		arg, value = line.split('=', 1)
		arg = arg.strip()
		value = value.strip()
		value = latex_to_unicode(value)

		if arg == 'Title':
			survey.title = value
		elif arg.startswith(QOBJECT_PREFIX):
			index, string = get_index_and_string(value)
			if index:
				auto_numbering_id = index + (0,)
			else:
				auto_numbering_id = auto_numbering_id[:-1] + (auto_numbering_id[-1] + 1,)
				index = auto_numbering_id

			qobject_type = arg[len(QOBJECT_PREFIX)+1:]

			qobject = getattr(model.questionnaire, qobject_type)
			assert issubclass(qobject, model.questionnaire.QObject)
			qobject = qobject()
			survey.questionnaire.add_qobject(qobject, new_id=index)
			qobject.setup.init()

			qobject.setup.question(string)
		elif arg.startswith(ANSWER_PREFIX):
			assert qobject is not None

			answer_type = arg[len(ANSWER_PREFIX)+1:]

			qobject.setup.answer(value)		
		elif arg == BOX:
			box = boxes.pop(0)
			# Sanity check, whether we got the correct box type.
			assert isinstance(box, getattr(model.questionnaire, value))

			qobject.setup.box(box)
		else:
			# Falltrough, it is some metadata:
			survey.info[arg] = value

	assert(len(boxes) == 0)


