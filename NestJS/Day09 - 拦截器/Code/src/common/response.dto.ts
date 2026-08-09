/**
 * 统一响应格式 DTO
 * 所有接口返回都包装为 { code, message, data } 结构
 * 由 TransformInterceptor 自动完成包装
 */
export class ResponseDto<T = any> {
  code: number;
  message: string;
  data: T;

  constructor(code: number, message: string, data: T) {
    this.code = code;
    this.message = message;
    this.data = data;
  }

  static success<T>(data: T, message = '请求成功'): ResponseDto<T> {
    return new ResponseDto<T>(200, message, data);
  }

  static error(code: number, message: string): ResponseDto<null> {
    return new ResponseDto<null>(code, message, null);
  }
}
