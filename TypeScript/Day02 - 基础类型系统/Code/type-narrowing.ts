// type-narrowing.ts
// 演示类型收窄：typeof 守卫、truthy 收窄、== null 收窄
// （本节为 Day05「类型守卫与收窄」详讲铺垫，此处只做初步介绍）

console.log('===== 1. typeof 守卫 =====');

// 在 if 分支内，TS 会根据 typeof 结果自动「收窄」类型
function padLeft(value: string | number, padding: string | number): string {
  if (typeof padding === 'number') {
    // 此处 padding 收窄为 number（排除了 string）
    return ' '.repeat(padding) + value;
  }
  // 此处 padding 收窄为 string
  return padding + value;
}

console.log('typeof 守卫 padLeft(5, 4) →', `[${padLeft(5, 4)}]`);
console.log('typeof 守卫 padLeft(5, ">>>") →', `[${padLeft(5, '>>>')}]`);

// 多类型联合的 typeof 收窄
function describe(v: string | number | boolean): string {
  if (typeof v === 'string') {
    // v 收窄为 string
    return '字符串：' + v.toUpperCase();
  }
  if (typeof v === 'number') {
    // v 收窄为 number
    return '数字：' + (v * 2);
  }
  // v 收窄为 boolean
  return '布尔：' + v;
}
console.log(describe('hi'));
console.log(describe(10));
console.log(describe(true));

console.log('\n===== 2. truthy 收窄 =====');

// 在 if (x) 中，TS 会排除 null / undefined / '' / 0 / false / NaN 等 falsy 值
function printAll(values: Array<string | null | undefined>): void {
  for (const v of values) {
    if (v) {
      // 此处 v 收窄为 string（排除了 null / undefined / ''）
      console.log('truthy 收窄后可调用 .toUpperCase →', v.toUpperCase());
    } else {
      // 此处 v 仍为 string | null | undefined
      console.log('falsy 值 →', v);
    }
  }
}
printAll(['a', null, '', undefined, 'b']);

console.log('\n===== 3. == null 收窄（同时排除 null 与 undefined） =====');

// == null 同时匹配 null 和 undefined（== undefined 同理，二者等价）
// 注意：=== null 只能排除 null，不能排除 undefined
function greet(name: string | null | undefined): string {
  if (name == null) {
    // 此处 name 同时排除 null 和 undefined
    return 'Hello, stranger';
  }
  // 此处 name 收窄为 string
  return 'Hello, ' + name.toUpperCase();
}
console.log(greet('Trae'));
console.log(greet(null));
console.log(greet(undefined));

// 对比 === null：只能排除 null，不能排除 undefined
function greetStrict(name: string | null | undefined): string {
  if (name === null) {
    return 'name is null';
  }
  // 此处 name 仍为 string | undefined（=== null 没排除 undefined）
  if (name === undefined) {
    return 'name is undefined';
  }
  // 此处 name 才收窄为 string
  return 'Hello, ' + name.toUpperCase();
}
console.log(greetStrict(null), '|', greetStrict(undefined), '|', greetStrict('Trae'));

console.log('\n===== 4. instanceof 收窄（补充） =====');

class Cat { meow() { return '喵'; } }
class Dog { bark() { return '汪'; } }
type Pet = Cat | Dog;

function speak(pet: Pet): string {
  if (pet instanceof Cat) {
    // pet 收窄为 Cat
    return pet.meow();
  }
  // pet 收窄为 Dog
  return pet.bark();
}
console.log('instanceof Cat →', speak(new Cat()));
console.log('instanceof Dog →', speak(new Dog()));

console.log('\n===== 5. in 操作符收窄（补充） =====');

type Fish = { swim: () => void };
type Bird = { fly: () => void };

function move(animal: Fish | Bird): string {
  if ('swim' in animal) {
    // animal 收窄为 Fish
    animal.swim();
    return '游泳';
  }
  // animal 收窄为 Bird
  animal.fly();
  return '飞翔';
}
console.log('in 操作符收窄 Fish →', move({ swim: () => {} }));
console.log('in 操作符收窄 Bird →', move({ fly: () => {} }));

console.log('\n===== 6. 收窄的实战：处理可能是 string 的数字 =====');

// 模拟从命令行 / 配置文件读取的值（往往是字符串）
function parsePort(input: string | number): number {
  // 收窄后分别处理
  if (typeof input === 'string') {
    const n = Number(input);
    if (Number.isNaN(n)) {
      throw new Error(`非法端口：${input}`);
    }
    return n;
  }
  return input;
}

console.log('parsePort("3000") →', parsePort('3000'));
console.log('parsePort(8080) →', parsePort(8080));
