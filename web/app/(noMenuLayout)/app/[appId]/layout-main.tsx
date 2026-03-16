// 对应 commonLayout 的文件: web/app/(commonLayout)/app/(appDetailLayout)/[appId]/layout-main.tsx
// 区别: 去除了 AppSideBar、导航配置、重定向逻辑、TagManagementModal
'use client'
import type { FC } from 'react'
import { useUnmount } from 'ahooks'
import React, { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useTranslation } from 'react-i18next'
import { useShallow } from 'zustand/react/shallow'
import { useStore } from '@/app/components/app/store'
import { fetchAppDetail } from '@/service/apps'
import { useAppContext } from '@/context/app-context'
import Loading from '@/app/components/base/loading'
import type { App } from '@/types/app'
import useDocumentTitle from '@/hooks/use-document-title'

export type IAppDetailNoMenuLayoutProps = {
  children: React.ReactNode
  appId: string
}

const AppDetailNoMenuLayout: FC<IAppDetailNoMenuLayoutProps> = (props) => {
  const {
    children,
    appId,
  } = props
  const { t } = useTranslation()
  const router = useRouter()
  const pathname = usePathname()
  const { isCurrentWorkspaceEditor, isLoadingCurrentWorkspace } = useAppContext()
  const { appDetail, setAppDetail } = useStore(useShallow(state => ({
    appDetail: state.appDetail,
    setAppDetail: state.setAppDetail,
  })))
  const [isLoadingAppDetail, setIsLoadingAppDetail] = useState(false)
  const [appDetailRes, setAppDetailRes] = useState<App | null>(null)

  useDocumentTitle(appDetail?.name || t('common.menus.appDetail'))

  useEffect(() => {
    setAppDetail()
    setIsLoadingAppDetail(true)
    fetchAppDetail({ url: '/apps', id: appId }).then((res) => {
      setAppDetailRes(res)
    }).catch((e: any) => {
      if (e.status === 404)
        router.replace('/apps')
    }).finally(() => {
      setIsLoadingAppDetail(false)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appId, pathname])

  useEffect(() => {
    if (!appDetailRes || isLoadingCurrentWorkspace || isLoadingAppDetail)
      return
    const res = appDetailRes
    setAppDetail({ ...res, enable_sso: false })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [appDetailRes, isCurrentWorkspaceEditor, isLoadingAppDetail, isLoadingCurrentWorkspace])

  useUnmount(() => {
    setAppDetail()
  })

  if (!appDetail) {
    return (
      <div className='flex h-full items-center justify-center bg-background-body'>
        <Loading />
      </div>
    )
  }

  return (
    <>
      {children}
    </>
  )
}
export default React.memo(AppDetailNoMenuLayout)
