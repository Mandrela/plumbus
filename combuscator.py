UNSAFE_CHARACTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_@"
ARITHMETIC_OP = ["+", "-", "*", "/", "%", "=", ">", "<", "|", "&", "^", "~", "(", ")", "[", "]", ":"]


class DebugFile:
	def __init__(self, filename:str , activated: bool = True, keepOpened: bool = True) -> None:
		self.active = activated
		self.keepOpened = keepOpened
		self.filename = filename
		self.filedesc = None
		self.clear()

	def __del__(self):
		self.close()

	def open(self):
		if not self.filedesc:
			self.filedesc = open(self.filename, "at")

	def close(self):
		if self.filedesc:
			self.filedesc.close()
			self.filedesc = None

	def clear(self):
		if not self.active:
			return
		self.close()
		self.filedesc = open(self.filename, "wt")
		if not self.keepOpened:
			self.close()

	def keepOpen(self, value: bool = True):
		self.keepOpened = value
		if self.keepOpened:
			self.open()

	def write(self, line: str):
		if not self.active:
			return
		if not self.keepOpened:
			self.open()
		self.filedesc.write(line)
		if not self.keepOpened:
			self.close()

	def writelines(self, lines: list[str]):
		if not self.active:
			return
		if not self.keepOpened:
			self.open()
		self.filedesc.writelines(lines)
		if not self.keepOpened:
			self.close()


def normalize(line: str) -> str:
	first_iteration = []
	last_letter = ' '
	string_env_s = False
	string_env_d = False
	for _ in range(len(line)): # delimits arithmetics not in string context
		letter = line[_]
		if letter == '#':
			break

		if letter == "'" and not string_env_d:
			string_env_s = not string_env_s
		if letter == '"' and not string_env_s:
			string_env_d = not string_env_d

		if letter in ARITHMETIC_OP and last_letter not in ARITHMETIC_OP and not string_env_s and not string_env_d:
			first_iteration.append(' ')

		first_iteration.append(letter)

		if letter in ARITHMETIC_OP and _ + 1 < len(line) and line[_ + 1] not in ARITHMETIC_OP and not string_env_s and not string_env_d:
			first_iteration.append(' ')

		last_letter = letter

	# print(first_iteration)
	newline = []
	identation = True
	last_letter = ''
	string_env_s = False
	string_env_d = False
	for letter in ''.join(first_iteration).rstrip(): # removes extra characters
		if letter == "'" and not string_env_d:
			string_env_s = not string_env_s
		if letter == '"' and not string_env_s:
			string_env_d = not string_env_d

		if letter not in " \t":
			newline.append(letter)
			identation = False
		elif last_letter not in " \t" or identation or string_env_s or string_env_d:
			newline.append(letter)

		last_letter = letter
	# print(newline)
	return ''.join(newline).rstrip()


def prepare_file(lines: list[str]) -> list[str]:
	lines = [line[:line.find('#')] for line in lines]

	_ = 0
	while _ < len(lines):
		if lines[_].strip() and lines[_].strip()[-1] == '\\':
			lines[_] = lines[_].rstrip()[:-1] + ' ' + lines.pop(_ + 1).strip()
			continue
		if '\"\"\"' in lines[_] \
				and "\'" in lines[_]:
			string_env_s = False
			string_env_d = False
			i = 0
			while i < len(lines[_]):
				if lines[_][i] == "'" and not string_env_d:
					string_env_s = not string_env_s
				if lines[_][i] == '"' and not string_env_s:
					string_env_d = not string_env_d

				if lines[_][i:i+3] == '\"\"\"' and string_env_s:
					lines[_] = lines[_][:i] + '\"\\\"\"' + lines[_][i + 3:]
					i += 4
				i += 1
		_ += 1

	_ = 0
	while _ < len(lines):
		if '\"\"\"' in lines[_]:

			newline = lines[_].replace('\"\"\"', '"')
			if lines[_].count('\"\"\"') % 2:
				while '\"\"\"' not in lines[_ + 1]:
					newline += '\\n' + lines.pop(_ + 1)
				newline += '\\n' + lines.pop(_ + 1).replace('\"\"\"', '"', 1)
			lines[_] = newline
			continue
		if lines[_].lstrip()[:4]  == "elif":
			print("found elif")
		print(lines[_])
		_ += 1

	# change var names
	# open elif
	# remove line breaks
	# multiline string
	# multiassignment
	return [line for line in map(normalize, lines) if line]


def tokenize(line: str) -> list[str]:
	line = line.strip()
	if line.startswith("if"): # elif does not exists at this point
		return ["if"] + line[2:-1].split() + [":"]
	elif line.startswith("else"):
		return ["else", ":"]
	if "'" not in line and \
			'"' not in line:
		return line.split()

	splitted_line = []
	word = ""
	string_env_s = False
	string_env_d = False
	for letter in line:
		if letter == '"' and not string_env_s:
			string_env_d = not string_env_d
		if letter == "'" and not string_env_d:
			string_env_s = not string_env_s

		if letter not in " \t" or string_env_s or string_env_d:
			word += letter
		elif last_letter not in " \t":
			splitted_line.append(word)
			word = ""

		last_letter = letter
	if word:
		splitted_line.append(word)
	return splitted_line


def compress(line: str) -> str: # unstripped but legit line on input
	return line.strip()


def determine_linetype(tokens: list[str]) -> str:
	if ' '.join(tokens).count("=") != 2 * ' '.join(tokens).count("=="):
		return "ass"
	elif tokens[0] in ["if", "else", "elif"]:
		return "ifel"
	elif tokens[0] == "import":
		return "import"
	elif tokens[0] == "def":
		return "def"
	elif tokens[0] == "class":
		return "class"
	elif tokens[0] == "for":
		return "for"
	elif tokens[0] == "while":
		return "while"
	return "nil"


def parse(lines: list[str], debug_file) -> str:
	out_line = ""
	line_buf = []

	# lines = list(map(normalize, lines + [""]))
	lines = prepare_file(lines + [""])
	debug_file.write("[\n") # WHAT
	# print("------------------------")

	_ = 0
	while _ < len(lines):
		line = lines[_]
		# print(tokenize(line))
		if line:
			tokens = tokenize(line)
			#print(tokens)
			linetype = determine_linetype(tokens)

			if linetype == "nil":
				debug_file.write(f"{linetype}:\t{line}\n")
				line_buf.append(compress(line))


			if linetype == "ifel":
				if tokens[0] != "if":
					raise Exception(f"Something wrong in ifel: {tokens[0]}")

				condition = ' '.join(tokens[1:-1])
				identcount = len(line) - len(line.strip())
				# print(f"condition: {condition}, ident: {identcount}")

				debug_file.write(f"{linetype}{identcount}:\t{line}\n")

				else_index = _ + 1
				while else_index < len(lines) and identcount < len(lines[else_index]) - len(lines[else_index].strip()) and \
						(lines[else_index].strip()[:4] != "else" or identcount != len(lines[else_index]) - len(lines[else_index].strip())):
					# print(lines[else_index], len(lines[else_index]) - len(lines[else_index].strip()))
					else_index += 1
				# print("kek", else_index)
				# print(tokenize(lines[else_index]))
				else_index = min(else_index, len(lines) - 1)

				else_line = "-0"
				else_end_index = else_index
				if lines[else_index] and tokenize(lines[else_index])[0] == "else" and identcount == len(lines[else_index]) - len(lines[else_index].strip()):
					# print(f"supplying else, ident: {identcount}")

					debug_file.write(f"else{identcount}:\t{lines[else_index]}\n")

					else_end_index += 1
					while else_end_index < len(lines) and identcount <  len(lines[else_end_index]) - len(lines[else_end_index].strip()):
						# print(lines[else_end_index], len(lines[else_end_index]) - len(lines[else_end_index].strip()))
						else_end_index += 1
					else_line = parse(lines[else_index + 1:else_end_index], debug_file)

				ifelse_line = "( " + parse(lines[_ + 1:else_index], debug_file) + " if "  + condition + " else " + else_line + " )"

				line_buf.append(compress(ifelse_line))
				_ = else_end_index - 1

			if linetype == "ass":
				debug_file.write(f"{linetype}:\t{line}\n")
				varname = line.split("=")
				print()
		_ += 1


	if len(line_buf):
		debug_file.write("]\n")
		out_line += ('[' + ','.join(line_buf) + ']' if len(line_buf) > 1 else ','.join(line_buf))

	return out_line


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(prog="combuscator", usage="combuscator [-d] <filename> <output>")
	parser.add_argument("-d", "--debug", action="store_true",
				help="Enable debug mode, **will create additional files!**")
	parser.add_argument("filename", action="store", type=str, help="Name of file to obfuscate")
	parser.add_argument("output", action="store", type=str, help="Obfuscated file name")
	args = parser.parse_args()


	open(args.output, "wt").write(parse(open(args.filename, "rt").readlines(),
					DebugFile(args.filename + ".debuginfo", args.debug)))


'''
Possible types:
independant lines (done), variable assignment
if-else junction (done), while loop, for loop (break, continue)
function definition, class definition, method definition
imports
'''

# (lambda NoneFunc: )(lambda *_: None)
