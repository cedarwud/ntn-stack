export const COORDINATE_TRANSFORM = {
    offsetX: 865,
    offsetY: 640,
    scale: 1.0,
}

export function imageToSceneCoords(
    mouseX: number,
    mouseY: number,
    renderedWidth: number,
    renderedHeight: number,
    naturalWidth: number,
    naturalHeight: number,
    transform = COORDINATE_TRANSFORM
): { x: number; y: number } | null {
    if (naturalWidth === 0 || naturalHeight === 0) return null;
    const ratioX = renderedWidth / naturalWidth;
    const ratioY = renderedHeight / naturalHeight;
    const actualScale = Math.min(ratioX, ratioY);
    const displayedImageWidth = naturalWidth * actualScale;
    const displayedImageHeight = naturalHeight * actualScale;
    const offsetX_render = (renderedWidth - displayedImageWidth) / 2;
    const offsetY_render = (renderedHeight - displayedImageHeight) / 2;
    const mouseXinDisplayed = mouseX - offsetX_render;
    const mouseYinDisplayed = mouseY - offsetY_render;
    if (
        mouseXinDisplayed < 0 ||
        mouseXinDisplayed > displayedImageWidth ||
        mouseYinDisplayed < 0 ||
        mouseYinDisplayed > displayedImageHeight
    ) {
        return null;
    }
    const originalImageX = mouseXinDisplayed / actualScale;
    const originalImageY = mouseYinDisplayed / actualScale;
    const sceneX = Math.round((originalImageX - transform.offsetX) / transform.scale);
    const sceneY = Math.round((originalImageY - transform.offsetY) / transform.scale);
    return { x: sceneX, y: sceneY };
}

export function sceneToImageCoords(
    sceneX: number,
    sceneY: number,
    imageRefElement: HTMLImageElement | null,
    imageNaturalSizeData: { width: number; height: number } | null,
    transform = COORDINATE_TRANSFORM
): { x: number; y: number } | null {
    if (!imageRefElement || !imageNaturalSizeData) return null;
    const { width: naturalWidth, height: naturalHeight } = imageNaturalSizeData;
    const renderedWidth = imageRefElement.offsetWidth;
    const renderedHeight = imageRefElement.offsetHeight;
    if (naturalWidth === 0 || naturalHeight === 0) return null;
    const originalImageX = sceneX * transform.scale + transform.offsetX;
    const originalImageY = sceneY * transform.scale + transform.offsetY;
    const ratioX = renderedWidth / naturalWidth;
    const ratioY = renderedHeight / naturalHeight;
    const actualScale = Math.min(ratioX, ratioY);
    const displayedImageWidth = naturalWidth * actualScale;
    const displayedImageHeight = naturalHeight * actualScale;
    const offsetX_render = (renderedWidth - displayedImageWidth) / 2;
    const offsetY_render = (renderedHeight - displayedImageHeight) / 2;
    const mouseXinDisplayed = originalImageX * actualScale;
    const mouseYinDisplayed = originalImageY * actualScale;
    const imageElementX = Math.round(mouseXinDisplayed + offsetX_render);
    const imageElementY = Math.round(mouseYinDisplayed + offsetY_render);
    return { x: imageElementX, y: imageElementY };
} 