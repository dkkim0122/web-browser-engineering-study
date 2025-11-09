import socket
import ssl
import tkinter
import tkinter.font

class URL:
  def __init__(self, url):
    self.scheme, url = url.split("://", 1)
    assert self.scheme in ["http", "https"] # 일단 http와 https만 지원하도록 함

    if "/" not in url:
      url = url + "/"
    self.host, url = url.split("/", 1)
    self.path = "/" + url

    if ":" in self.host:
      self.host, port = self.host.split(":", 1)
      self.port = int(port)
    
    # 연결에 따른 포트 지정
    if self.scheme == "http":
      self.port = 80
    elif self.scheme == "https":
      self.port = 443
    
    # 사용자 지정 포트 파싱하기
    if ":" in self.host:
      self.host, port = self.host.split(":", 1)
      self.port = int(port)

  def request(self):
    # 소켓 생성
    s = socket.socket(
      family=socket.AF_INET,
      type=socket.SOCK_STREAM,
      proto=socket.IPPROTO_TCP,
    )

    # 소켓 연결
    s.connect((self.host, self.port))

    if self.scheme == "https":
      ctx = ssl.create_default_context()
      s = ctx.wrap_socket(s, server_hostname=self.host)

    request = "GET {} HTTP/1.0\r\n".format(self.path)
    request += "Host: {}\r\n".format(self.host) # 줄바꿈을 위해 \r이 아니라 \r\n을 사용해야 한다.
    request += "\r\n" # 무조건 \r\n을 두번 보내야 한다.
    s.send(request.encode("utf-8")) # 바이트열로 변환하여 전송

    # 응답 수신
    response = s.makefile("r", encoding="utf-8", newline="\r\n") # HTTP의 줄바꿈은 \r\n 이므로 newline="\r\n" 으로 지정

    # 상태 라인 읽기
    statusline = response.readline() # 상태 라인 읽기
    version, status, explanation = statusline.split(" ", 2) # 상태 라인 파싱

    # 헤더 읽기
    response_headers = {}
    while True:
      line = response.readline()
      if line == "\r\n": # 헤더의 끝은 빈 줄로 표시된다.
        break
      header, value = line.split(":", 1)
      response_headers[header.casefold()] = value.strip() # 헤더 이름은 대소문자를 구분하지 않으므로 casefold() 사용하여 소문자로 통일

    assert "transfer-encoding" not in response_headers
    assert "content-encoding" not in response_headers

    # 본문 읽기
    body = response.read()
    s.close() # 소켓 닫기
    return body

class Text:
  def __init__(self, text):
    self.text = text

class Tag:
  def __init__(self, tag):
    self.tag = tag


def lex(body):
  out = []
  buffer = "" # 태그의 컨텐츠나 텍스트를 임시로 저장하는 버퍼
  in_tag = False
  for c in body:
    if c == "<":
      in_tag = True
      if buffer: out.append(Text(buffer))
      buffer = ""
    elif c == ">":
      in_tag = False
      out.append(Tag(buffer))
      buffer = ""
    elif not in_tag:
      buffer += c
  if not in_tag and buffer:
    out.append(Text(buffer))
  return out

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100

class Layout:
  def __init__(self, tokens):
    self.display_list = []
    self.cursor_x, self.cursor_y = HSTEP, VSTEP
    self.weight = "normal"
    self.style = "roman"
    self.size = 12

    for tok in tokens:
      self.token(tok)
  
  def token(self, tok):
    if isinstance(tok, Text): # 텍스트만 화면에 표시해야 함
      for word in tok.text.split():
        self.word(word)
    elif tok.tag == "i":
      self.style = "italic"
    elif tok.tag == "/i":
      self.style = "roman"
    elif tok.tag == "b":
      self.weight = "bold"
    elif tok.tag == "/b":
      self.weight = "normal"
    elif tok.tag == "small":
      self.size -= 2
    elif tok.tag == "/small":
      self.size += 2
    elif tok.tag == "big":
      self.size += 4
    elif tok.tag == "/big":
      self.size -= 4

  def word(self, word):
    font = tkinter.font.Font(
      size=self.size,
      weight=self.weight, 
      slant=self.style,
    )
    # 각 단어의 너비 계산
    w = font.measure(word)

    # 줄 바꿈 처리
    if self.cursor_x + w >= WIDTH - HSTEP:
      self.cursor_y += font.metrics("linespace") * 1.25 # 약간의 세로 여백을 위해 1.25 곱하기
      self.cursor_x = HSTEP

    # 지금 단어 기억 후 다음 단어로 이동
    self.display_list.append((self.cursor_x, self.cursor_y, word))
    self.cursor_x += w + font.measure(" ") # 단어 너비 + 공백 너비

class Browser: 
  def __init__(self):
    self.window = tkinter.Tk()
    self.canvas = tkinter.Canvas(
      self.window, 
      width=WIDTH, 
      height=HEIGHT
    )
    self.canvas.pack()

    # 스크롤
    self.scroll = 0 # 스크롤한 거리
    self.window.bind("<Down>", self.scrolldown) # 아래 화살표 키 바인딩

  def load(self, url):
    body = url.request()
    tokens = lex(body)
    self.display_list = Layout(tokens).display_list
    self.draw()   
  
  def draw(self):
    self.canvas.delete("all") # 캔버스 초기화
    for x, y, c in self.display_list:
      # 보이지 않는 부분은 그리지 않음
      if y > self.scroll + HEIGHT: continue # 창의 아래 부분
      if y + VSTEP < self.scroll: continue # 창의 위의 부분

      # 그리기
      self.canvas.create_text(x, y - self.scroll, text=c)
  
  # 아래로 스크롤 이벤트 핸들러
  def scrolldown(self, e):
    self.scroll += SCROLL_STEP
    self.draw()

# 커맨드 라인에서 실행할 때 load 함수 실행
if __name__ == "__main__":
  import sys
  Browser().load(URL(sys.argv[1])) # 커맨드 라인 인수를 URL 객체로 변환하여 load 함수에 전달
  tkinter.mainloop()
