// 文件用途：calculator 的基准测试，演示 b.ResetTimer 与 benchmem
// 运行方式：go test -bench=. -benchmem ./calc
package calc

import "testing"

// benchSink 防止编译器把基准测试的计算优化掉。
var benchSink float64

func BenchmarkAdd(b *testing.B) {
	var total float64
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		total = Add(total, float64(i%100))
	}
	benchSink = total
}

func BenchmarkAverage(b *testing.B) {
	nums := make([]float64, 1000)
	for i := range nums {
		nums[i] = float64(i)
	}

	b.ResetTimer()
	var total float64
	for i := 0; i < b.N; i++ {
		avg, err := Average(nums)
		if err != nil {
			b.Fatal(err)
		}
		total += avg
	}
	benchSink = total
}
