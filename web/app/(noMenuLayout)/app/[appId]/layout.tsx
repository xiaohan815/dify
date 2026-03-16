// 对应 commonLayout 的文件: web/app/(commonLayout)/app/(appDetailLayout)/[appId]/layout.tsx
// 区别: 无区别，都是服务器组件包装器，将 appId 传递给 layout-main.tsx
import Main from './layout-main'

const AppDetailLayout = async (props: {
  children: React.ReactNode
  params: Promise<{ appId: string }>
}) => {
  const {
    children,
    params,
  } = props

  return <Main appId={(await params).appId}>{children}</Main>
}
export default AppDetailLayout
