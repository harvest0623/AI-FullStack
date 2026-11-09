// 文件用途：calculator 的表驱动单元测试与示例测试
// 运行方式：go test ./calc
package calc

import (
	"errors"
	"fmt"
	"math"
	"testing"
)

const epsilon = 1e-9

// assertFloat 比较浮点结果；t.Helper 让失败信息指向调用处而不是本函数。
func assertFloat(t *testing.T, got, want float64) {
	t.Helper()
	if math.Abs(got-want) > epsilon {
		t.Fatalf("got %.10f, want %.10f", got, want)
	}
}

func TestAdd(t *testing.T) {
	tests := []struct {
		name string
		a    float64
		b    float64
		want float64
	}{
		{name: "正数相加", a: 1.5, b: 2.5, want: 4},
		{name: "正负相加", a: 10, b: -3, want: 7},
		{name: "与零相加", a: 0, b: 0, want: 0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assertFloat(t, Add(tt.a, tt.b), tt.want)
		})
	}
}

func TestSubtract(t *testing.T) {
	tests := []struct {
		name string
		a    float64
		b    float64
		want float64
	}{
		{name: "正数相减", a: 5, b: 2, want: 3},
		{name: "结果为负", a: 2, b: 5, want: -3},
		{name: "减去零", a: 7, b: 0, want: 7},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assertFloat(t, Subtract(tt.a, tt.b), tt.want)
		})
	}
}

func TestDivide(t *testing.T) {
	tests := []struct {
		name    string
		a       float64
		b       float64
		want    float64
		wantErr error
	}{
		{name: "整除", a: 10, b: 2, want: 5},
		{name: "小数结果", a: 1, b: 4, want: 0.25},
		{name: "除数为零", a: 1, b: 0, wantErr: ErrDivideByZero},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := Divide(tt.a, tt.b)
			if tt.wantErr != nil {
				if !errors.Is(err, tt.wantErr) {
					t.Fatalf("got error %v, want %v", err, tt.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			assertFloat(t, got, tt.want)
		})
	}
}

func TestAverage(t *testing.T) {
	tests := []struct {
		name    string
		nums    []float64
		want    float64
		wantErr error
	}{
		{name: "单个元素", nums: []float64{8}, want: 8},
		{name: "多个元素", nums: []float64{1, 2, 3, 4}, want: 2.5},
		{name: "空切片", nums: nil, wantErr: ErrEmptySlice},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := Average(tt.nums)
			if tt.wantErr != nil {
				if !errors.Is(err, tt.wantErr) {
					t.Fatalf("got error %v, want %v", err, tt.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			assertFloat(t, got, tt.want)
		})
	}
}

// ExampleAdd 演示示例测试：注释中的 Output 会与标准输出逐行比对。
func ExampleAdd() {
	fmt.Println(Add(2, 3))
	// Output: 5
}
