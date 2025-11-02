import socket

class URL:
  def __init__(self, url):
    self.scheme, url = url.split("://", 1)
    assert self.scheme == "http" # 일단 http만 지원하도록 함

    if "/" not in url:
      url = url + "/"
    self.host, url = url.split("/", 1)
    self.path = "/" + url

  def request(self):
    # 소켓 생성
    s = socket.socket(
      family=socket.AF_INET,
      type=socket.SOCK_STREAM,
      proto=socket.IPPROTO_TCP,
    )

    # 소켓 연결
    s.connect((self.host, 80))

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