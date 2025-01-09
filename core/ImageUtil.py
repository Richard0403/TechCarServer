import os

from PIL import Image, ImageDraw, ImageFont


def add_device_id_to_qrcode(origin_img: str, device_id: str, del_origin_after_handle=False) -> str:
    # 打开原始图片
    original_img = Image.open(origin_img)

    # 创建450x450的白色背景
    background = Image.new("RGB",
                           (int(original_img.width * 1.6), int(original_img.height * 1.1)),
                           (255, 255, 255))

    # 计算图片粘贴的左上角位置，使图片居中
    x_offset = (background.width - original_img.width) // 2
    y_offset = 0

    # 在背景上粘贴原始图片
    background.paste(original_img, (x_offset, y_offset))

    # 添加文字
    draw = ImageDraw.Draw(background)
    text = device_id
    font = ImageFont.load_default(40)  # 你也可以加载自定义字体
    text_width = draw.textlength(text, font=font)

    # 在底部居中绘制文字
    text_x = (background.width - text_width) // 2
    text_y = background.height - 50  # 离底部10像素的位置

    draw.text((text_x, text_y), text, fill="black", font=font)

    font = ImageFont.truetype("font/simhei.ttf", 120)  # 20是字体大小
    draw.text((20, background.height / 2 - 200), '扫', fill=(255, 0, 0), font=font)
    draw.text((20, background.height / 2 + 40), '码', fill=(255, 0, 0), font=font)
    draw.text((background.width - 130, background.height / 2 - 200), '开', fill=(255, 0, 0), font=font)
    draw.text((background.width - 130, background.height / 2 + 40), '车', fill=(255, 0, 0), font=font)
    # 保存最终图片
    output_file = "qr_code/output_image.png"
    background.save(output_file)
    if del_origin_after_handle and os.path.exists(origin_img):
        os.remove(origin_img)
    return output_file


if __name__ == '__main__':
    add_device_id_to_qrcode('qr_code88076f27-a63d-415d-965c-34e8e486b215.png', '863644071795703')
