/**
 * 爬取全国三甲医院，包括地址
 * 
 * 数据来自：
 * http://www.a-hospital.com/w/%E5%85%A8%E5%9B%BD%E4%B8%89%E7%94%B2%E5%8C%BB%E9%99%A2%E5%90%8D%E5%8D%95
 * 
 * 代码用于直接在网页环境中执行
 * 
 * 1335个含有地址的医院
 * 
 * 北京市下，13个部队医院
 * 
 * 结尾包含部队医院
 * 参考列表会被选择
 * 
 * 注意:
 * NodeList是类数组对象，转化后才能使用全部数组方法
 * 
 * :scope refer to the current context
 * In some of the latest browsers (Chrome, Firefox 32+, Opera 15+, and Safari 7.0+) 
 * you can use the :scope selector in calls to querySelector and querySelectorAll
 * 
 * 导出后，手动删除电话号码、添加北京市部队医院的地址、删除结尾的无关数据
 */

// 保存结果的数组
let resultList = new Array();

// 选择所有的列表条目
/** @type {Array<HTMLLIElement>} */
let liList = Array.from(document.querySelectorAll('#bodyContent > ul > li'));
liList.forEach(liElement => {
    // 选择存在地址的条目

    /** @type {HTMLElement} */
    let nameElement = liElement.querySelector(':scope > b:nth-child(1)');

    let name, address;

    if (nameElement) {
        name = nameElement.innerText;

        /** @type {HTMLElement} */
        let addressElement = liElement.querySelector(':scope > ul > li:first-child');
        address = addressElement.innerText;
        address = address.replace('医院地址：', '');
    }
    else {
        // 对于不存在地址的条目
        name = liElement.innerText;
        address = '';
    }

    resultList.push({ name, address });

});

console.log(JSON.stringify(resultList));