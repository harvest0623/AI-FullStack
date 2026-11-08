// 文件用途：演示 io.Reader/io.Writer 抽象与组合：strings.Reader、bytes.Buffer、io.Copy、
// io.TeeReader、io.LimitReader 与自定义 Writer
// 运行方式：go run io_interfaces.go
package main

import (
	"bytes"
	"fmt"
	"io"
	"strings"
)

// upperWriter 把写入内容转成大写后转发给底层 Writer。
type upperWriter struct {
	dst io.Writer
}

// Write 实现 io.Writer 接口。
func (w *upperWriter) Write(p []byte) (int, error) {
	return w.dst.Write([]byte(strings.ToUpper(string(p))))
}

// countWriter 统计写入字节数，同时转发给底层 Writer。
type countWriter struct {
	dst   io.Writer
	bytes int
}

// Write 实现 io.Writer 接口。
func (w *countWriter) Write(p []byte) (int, error) {
	n, err := w.dst.Write(p)
	w.bytes += n
	return n, err
}

func main() {
	fmt.Println("=== 1. strings.Reader：把字符串当成 Reader ===")
	r := strings.NewReader("p1001,iPhone 15,5999\n")
	buf := make([]byte, 8)
	n, err := r.Read(buf)
	fmt.Printf("第一次读 %d 字节：%q，err=%v\n", n, buf[:n], err)
	rest, err := io.ReadAll(r)
	if err != nil {
		fmt.Println("读取失败：", err)
		return
	}
	fmt.Printf("剩余内容：%q\n", rest)

	fmt.Println("\n=== 2. bytes.Buffer：既是 Reader 又是 Writer ===")
	var b bytes.Buffer
	fmt.Fprintf(&b, "商品：%s，价格：%.2f\n", "iPhone 15", 5999.0)
	b.WriteString("库存：120\n")
	fmt.Printf("缓冲内容（%d 字节）：\n%s", b.Len(), b.String())
	line, err := b.ReadString('\n')
	if err != nil {
		fmt.Println("读取失败：", err)
		return
	}
	fmt.Printf("ReadString 读到第一行：%q\n", line)

	fmt.Println("\n=== 3. io.Copy：Reader -> Writer ===")
	src := strings.NewReader("eshop-gateway 正在聚合上游 LLM 响应\n")
	var dst bytes.Buffer
	written, err := io.Copy(&dst, src)
	if err != nil {
		fmt.Println("拷贝失败：", err)
		return
	}
	fmt.Printf("拷贝 %d 字节到目标：%s", written, dst.String())

	fmt.Println("\n=== 4. io.TeeReader：边读边复制（日志/审计） ===")
	body := strings.NewReader(`{"order":"o9001","amount":25998}`)
	var audit bytes.Buffer
	tee := io.TeeReader(body, &audit)
	decoded, err := io.ReadAll(tee)
	if err != nil {
		fmt.Println("读取失败：", err)
		return
	}
	fmt.Printf("业务读到：%s\n", decoded)
	fmt.Printf("审计副本：%s\n", audit.String())

	fmt.Println("\n=== 5. io.LimitReader：限制最多读取字节数 ===")
	long := strings.NewReader(strings.Repeat("A", 100))
	limited := io.LimitReader(long, 16)
	head, err := io.ReadAll(limited)
	if err != nil {
		fmt.Println("读取失败：", err)
		return
	}
	fmt.Printf("只读取前 %d 字节：%q\n", len(head), head)

	fmt.Println("\n=== 6. 自定义 Writer 组合 ===")
	var out bytes.Buffer
	counter := &countWriter{dst: &out}
	upper := &upperWriter{dst: counter}
	if _, err := io.WriteString(upper, "eshop llm gateway\n"); err != nil {
		fmt.Println("写入失败：", err)
		return
	}
	fmt.Printf("自定义 Writer 输出：%q\n", out.String())
	fmt.Printf("统计写入字节数：%d\n", counter.bytes)

	// io.Writer 只有一个 Write 方法；满足它的类型可以任意组合、嵌套。
	var w io.Writer = upper
	fmt.Printf("upperWriter 满足 io.Writer：%T\n", w)
}
