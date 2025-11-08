import socket
import ssl

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
  
def show(body):
  in_tag = False
  for c in body:
    if c == "<":
      in_tag = True
    elif c == ">":
      in_tag = False
    elif not in_tag:
      print(c, end="") # 태그 안에 있지 않은 문자만 출력

# 웹페이지 로드
def load(url):
  body = url.request()
  show(body)

# 커맨드 라인에서 실행할 때 load 함수 실행
if __name__ == "__main__":
  import sys
  load(URL(sys.argv[1])) # 커맨드 라인 인수를 URL 객체로 변환하여 load 함수에 전달